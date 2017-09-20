import asyncio
import sys
import time
from contextlib import contextmanager

from .exceptions import RconCommandFailed
from .parser import CombinedParser, StatusItemParser, CvarParser
from .protocol import create_rcon_protocol, RCON_NOSECURE

__all__ = ['BaseRconClient']


class BaseRconClient:
    def __init__(self, loop, remote_host, remote_port, password=None, secure=RCON_NOSECURE,
                 poll_status_interval=6, log_listener_ip=None):
        self.loop = loop
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.secure = secure
        self.password = password
        self.poll_status_interval = poll_status_interval
        self.log_listener_ip = log_listener_ip
        self.cmd_transport = self.cmd_protocol = self.log_transport = self.log_protocol = None
        self.status = {}
        self.cvars = {}
        self.cmd_timestamp = 0
        self.log_timestamp = 0
        self.admin_nick = ''
        self.log_parser = CombinedParser(self, dump_to=sys.stdout.buffer)
        self.cmd_parser = CombinedParser(self, parsers=[StatusItemParser, CvarParser])
        self.connected = False

    def check_connection(self, timeout=60):
        if self.log_listener_ip:
            return self.status and time.time() - self.log_timestamp < timeout
        else:
            return bool(self.status)

    def on_server_connected(self):
        self.send('sv_adminnick')

    def on_server_disconnected(self):
        pass

    async def connect_forever(self, connect_log=False):
        while True:
            if not self.check_connection():
                if self.connected:
                    self.connected = False
                    self.on_server_disconnected()
                self.connected = await self.connect_once(connect_log)
                if self.connected:
                    self.on_server_connected()
            else:
                await self.update_server_status()
            asyncio.sleep(self.poll_status_interval)

    async def connect_once(self, connect_log=False):
        self.cmd_transport, self.cmd_protocol = await self._connect(self.cmd_data_received)
        status = await self.update_server_status()
        if connect_log and status:
            self.log_transport, self.log_protocol = await self._connect(self.log_data_received)
            self.subscribe_to_log()
            await self.cleanup_log_dest_udp()
        return status

    async def _connect(self, callback):
        protocol_class = create_rcon_protocol(self.password, self.secure, callback)
        return await self.loop.create_datagram_endpoint(protocol_class,
                                                        remote_addr=(self.remote_host, self.remote_port))

    def subscribe_to_log(self):
        self.send("sv_cmd addtolist log_dest_udp %s:%s" % (self.log_protocol.local_host, self.log_protocol.local_port))
        self.send("sv_logscores_console 0")
        self.send("sv_logscores_bots 1")
        self.send("sv_eventlog 1")
        self.send("sv_eventlog_console 1")

    async def cleanup_log_dest_udp(self):
        self.cvars['log_dest_udp'] = None
        try:
            await self.execute_with_retry('log_dest_udp', lambda: self.cvars['log_dest_udp'] is None)
        except RconCommandFailed:
            return
        for i in self.cvars['log_dest_udp'].split(' '):
            host, port = i.rsplit(':', 1)
            if host == self.log_listener_ip and int(port) != self.log_protocol.local_port:
                self.send('sv_cmd removefromlist log_dest_udp %s' % i)

    async def update_server_status(self):
        try:
            await self.execute_with_retry('status 1', lambda: 'players' in self.status)
        except RconCommandFailed:
            return False
        else:
            return True

    @contextmanager
    def sv_adminnick(self, new_nick):
        old_nick = self.cvars['sv_adminnick'] or ''
        self.send('sv_adminnick "%s"' % new_nick)
        yield
        self.send('sv_adminnick "%s"' % old_nick)

    def send(self, command):
        self.cmd_protocol.send(command)

    def cmd_data_received(self, data, addr):
        # TODO: resolve self.remote host to IP
        if addr[0] != self.remote_host or addr[1] != self.remote_port:
            return
        self.cmd_timestamp = time.time()
        self.cmd_parser.feed(data)

    def log_data_received(self, data, addr):
        if addr[0] != self.remote_host or addr[1] != self.remote_port:
            return
        self.log_timestamp = time.time()
        self.log_parser.feed(data)

    async def execute(self, command, timeout=1):
        self.cmd_parser.dump_to = sys.stdout.buffer
        self.send(command)
        asyncio.sleep(timeout)
        self.cmd_parser.dump_to = None

    async def execute_with_retry(self, command, condition, retries=3, timeout=3):
        self.send(command)
        t = time.time()
        interval = timeout / retries
        while not condition() and retries > 0:
            await asyncio.sleep(0.1)
            if time.time() - t > interval:
                self.send(command)
                retries -= 1
                t = time.time()

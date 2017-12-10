import random
from unittest.mock import Mock

from aio_dprcon.protocol import *


def test_ensure_bytes():
    assert ensure_bytes('hello') == b'hello'
    assert ensure_bytes(b'hello') == b'hello'


def test_rcon_nosecure_packet():
    p = rcon_nosecure_packet('12345', 'status 1')
    assert p == QUAKE_PACKET_HEADER + b'rcon 12345 status 1'


def test_rcon_secure_time_packet():
    p = rcon_secure_time_packet('12345', 'status 1')
    assert p.startswith(QUAKE_PACKET_HEADER)
    assert b'srcon' in p


def test_parse_rcon_response():
    r = parse_rcon_response(b'\xff\xff\xff\xffnhello')
    assert r == b'hello'


class MockTransport:
    sendto = Mock()

    def get_extra_info(self, *args):
        return '127.0.0.1', random.randint(10000, 60000)


def test_protocol_nosecure(dummy_status):
    received_callback = Mock()
    connected_callback = Mock()
    rp = create_rcon_protocol('12345', 0, received_callback, connected_callback)()
    rp.connection_made(MockTransport())
    assert connected_callback.called
    rp.datagram_received(RCON_RESPONSE_HEADER + dummy_status, ('127.0.0.1', 26000))
    assert received_callback.called
    assert received_callback.call_args[0][0] == dummy_status
    assert received_callback.call_args[0][1] == ('127.0.0.1', 26000)
    rp.send('status 1')
    assert rp.transport.sendto.called
    assert rp.transport.sendto.call_args[0][0] == QUAKE_PACKET_HEADER + b'rcon 12345 status 1'


def test_protocol_secure_time():
    received_callback = Mock()
    connected_callback = Mock()
    rp = create_rcon_protocol('12345', 1, received_callback, connected_callback)()
    rp.connection_made(MockTransport())
    rp.send('status 1')
    assert rp.transport.sendto.called
    msg = rp.transport.sendto.call_args[0][0]
    assert msg.startswith(QUAKE_PACKET_HEADER)
    assert b'srcon' in msg

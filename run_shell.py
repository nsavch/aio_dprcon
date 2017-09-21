import asyncio

from aio_dprcon.shell import RconShell
from aio_dprcon.client import RconClient


if __name__ == '__main__':
    client = RconClient(asyncio.get_event_loop(), '127.0.0.1', 26000, password='password', secure=1)
    shell = RconShell(client)
    shell.cmdloop()

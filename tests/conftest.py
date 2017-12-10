import asyncio
import asynctest

import pytest
from click.testing import CliRunner

from aio_dprcon.client import RconClient


@pytest.fixture()
def cli_runner():
    """
    Provides click runner object
    """
    return CliRunner()


@pytest.fixture()
def loop():
    loop = asyncio.new_event_loop()
    loop.create_datagram_endpoint = asynctest.CoroutineMock(return_value=(None, None))
    return loop


@pytest.fixture()
def rcon_client(loop, mocker):
    c = RconClient(loop, '127.0.0.1', 26000, '12345', secure=1)
    mocker.patch.object(c, 'send')
    return c


@pytest.fixture()
def dummy_status():
    return b'host:     exe.pub | Relaxed Running | CTS/XDF\nversion:  Xonotic build 20:43:18 Apr 30 2017 - release (gamename Xonotic)\nprotocol: 3504 (DP7)\nmap:      inder-whoot2\ntiming:   6.7% CPU, 0.00% lost, offset avg 0.2ms, max 6.2ms, sdev 0.5ms\nplayers:  0 active (16 max)\n\n^2IP                                             %pl ping  time   frags  no   name\n'

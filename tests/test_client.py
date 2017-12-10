import asyncio
import time


def test_connect_once(loop, rcon_client, dummy_status):
    async def __send_status_data(c):
        await asyncio.sleep(0.5)
        c.cmd_data_received(dummy_status, (c.remote_host, c.remote_port))
        await asyncio.sleep(1)

    assert rcon_client.loop is loop
    loop.run_until_complete(asyncio.gather(rcon_client.connect_once(),
                                           __send_status_data(rcon_client),
                                           loop=loop))
    time.sleep(1)
    assert loop.create_datagram_endpoint.called
    assert rcon_client.connected


def test_connect_forever(loop, rcon_client, dummy_status):
    assert rcon_client.loop is loop

    async def __send_status_data(c):
        await asyncio.sleep(0.5)
        c.cmd_data_received(dummy_status, (c.remote_host, c.remote_port))
        await asyncio.sleep(5)

    tasks = [rcon_client.connect_forever(),
             __send_status_data(rcon_client)
             ]

    finished, pending = loop.run_until_complete(
        asyncio.wait(tasks, loop=loop, return_when=asyncio.FIRST_COMPLETED))
    for task in pending:
        task.cancel()

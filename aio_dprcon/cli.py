import asyncio

import click

from .config import Config, ServerConfigItem
from .shell import RconShell
from .client import RconClient


@click.group()
@click.help_option()
@click.version_option()
def cli():
    pass


@cli.command()
def servers():
    config = Config.load()
    if config.servers:
        print('Servers:')
        for i in config.servers:
            print('  * {0.name}: {0.host}:{0.port}'.format(i))
    else:
        print('No servers defined. Use "aio_dprcon add" to add a server')


@cli.command()
def add():
    config = Config.load()
    server = ServerConfigItem.from_input()
    config.add_server(server)
    config.save()


@cli.command()
def remove():
    pass


@cli.command()
@click.argument('server_name')
def connect(server_name):
    config = Config.load()
    server = config.get_server(server_name)
    completions = server.load_completions()
    rcon_client = RconClient(asyncio.get_event_loop(),
                             server.host,
                             server.port,
                             password=server.password,
                             secure=server.secure)
    if completions:
        rcon_client.completions = completions
    shell = RconShell(rcon_client)
    shell.cmdloop()


@cli.command()
@click.argument('server_name')
def refresh(server_name):
    config = Config.load()
    server = config.get_server(server_name)
    loop = asyncio.get_event_loop()
    rcon_client = RconClient(loop,
                             server.host,
                             server.port,
                             password=server.password,
                             secure=server.secure)
    loop.run_until_complete(rcon_client.connect_once())
    loop.run_until_complete(rcon_client.load_completions())
    server.update_completions(rcon_client.completions)


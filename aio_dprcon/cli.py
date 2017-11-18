import asyncio
import sys

import click

from .config import Config, ServerConfigItem
from .shell import RconShell


@click.group()
@click.help_option()
@click.version_option()
def cli():
    pass


@cli.command()
@click.pass_context
def servers(ctx):
    """
    Lists servers
    """
    config = Config.load()
    if config.servers:
        click.secho('Servers:', fg='green', bold=True)
        for server in config.servers.values():
            click.echo('  * {0.name}: {0.host}:{0.port}'.format(server))
    else:
        click.secho('No servers defined. Use "{} add" to add a server'.format(ctx.parent.command_path), fg='red', bold=True)


@cli.command()
def add():
    """
    Add a server (interactively)
    """
    config = Config.load()
    server = ServerConfigItem.from_input()
    config.add_server(server)
    config.save()


@cli.command()
@click.argument('server_name')
def remove(server_name):
    """
    Remove a server SERVER_NAME
    """
    config = Config.load()
    server = config.get_server(server_name)
    confirm = input('Are you sure to remove {0.name}: {0.host}:{0.port}? (y/N): '.format(server))
    if confirm[0] in ('y', 'Y'):
        config.remove_server(server_name)
        config.save()


@cli.command()
@click.argument('server_name')
def connect(server_name):
    """
    Connect to a server SERVER_NAME
    """
    config = Config.load()
    server = config.get_server(server_name)
    completions = server.load_completions()
    rcon_client = server.get_client()
    if completions:
        rcon_client.completions = completions
    shell = RconShell(server, rcon_client)
    shell.cmdloop()


@cli.command()
@click.argument('server_name')
def refresh(server_name):
    """
    Refresh completions cache for SERVER_NAME
    """
    config = Config.load()
    server = config.get_server(server_name)
    loop = asyncio.get_event_loop()
    rcon_client = server.get_client(loop)
    loop.run_until_complete(rcon_client.connect_once())
    loop.run_until_complete(rcon_client.load_completions())
    server.update_completions(rcon_client.completions)


import os
import cmd
import signal
import sys

import atexit
import click
import dpcolors
import readline


# TODO: connection activity indicator (if possible)


class RconShell(cmd.Cmd):
    def __init__(self, server, rcon_client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = rcon_client
        self.loop = self.client.loop
        self.completion_matches = []
        self.data = b''
        self.server = server
        signal.signal(signal.SIGINT, self.abort)
        self.history_file = os.path.expanduser('~/.config/aio_dprcon/history.{}'.format(self.server.name))
        self.init_history()

    def init_history(self):
        if os.path.exists(self.history_file):
            readline.read_history_file(self.history_file)
        atexit.register(self.save_history)

    def save_history(self):
        readline.set_history_length(2048)
        readline.write_history_file(self.history_file)

    def data_cb(self, data, addr):
        self.data += data

    def preloop(self):
        self.loop.run_until_complete(self.client.connect_once())
        if not self.client.connected:
            click.secho('Could not connect to server.', fg='red')
            sys.exit(1)
        self.prompt = '{} > '.format(click.style(self.client.status['host'],
                                                 fg='green',
                                                 bold=True))
        self.client.custom_cmd_callback = self.data_cb

    def abort(self, signal, frame):
        self.onecmd('')

    def do_exit(self, line):
        if line == 'EOF':
            print()
        click.secho('Good Riddance!', fg='blue', bold=True)
        sys.exit(0)

    def do_refresh(self, line):
        pass

    def run_special(self, line):
        if line in ('EOF', 'exit', 'quit'):
            self.do_exit(line)
        if line.startswith('%'):
            func = getattr(self, 'do_' + line[1:], None)
            if func:
                func(line[1:])
            else:
                click.secho('No such special function: {}'.format(line))
            return True

    def onecmd(self, line):
        if line:
            if self.run_special(line):
                return
            self.loop.run_until_complete(self.client.execute(line, timeout=1))
            cs = dpcolors.ColorString.from_dp(self.data)
            sys.stdout.buffer.write(cs.to_ansi_8bit())
            sys.stdout.flush()
            self.data = b''

    def complete(self, text, state):
        if state == 0:
            origline = readline.get_line_buffer()
            line = origline.lstrip()
            stripped = len(origline) - len(line)
            begidx = readline.get_begidx() - stripped
            endidx = readline.get_endidx() - stripped
            self.completion_matches = []
            if begidx == 0:
                for type_ in ('cvar', 'alias', 'command'):
                    self.completion_matches += [i for i in self.client.completions[type_].keys() if i.startswith(text)]
                self.completion_matches.sort()
        try:
            return self.completion_matches[state]
        except IndexError:
            return None

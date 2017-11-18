
import cmd
import sys

import dpcolors


class RconShell(cmd.Cmd):
    def __init__(self, rcon_client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = rcon_client
        self.loop = self.client.loop
        self.completion_matches = []
        self.data = b''

    def data_cb(self, data, addr):
        self.data += data

    def preloop(self):
        self.loop.run_until_complete(self.client.connect_once())
        self.client.custom_cmd_callback = self.data_cb

    def onecmd(self, line):
        if line:
            self.loop.run_until_complete(self.client.execute(line, timeout=1))
            cs = dpcolors.ColorString.from_dp(self.data)
            sys.stdout.buffer.write(cs.to_ansi_8bit())
            sys.stdout.flush()
            self.data = b''

    def complete(self, text, state):
        if state == 0:
            import readline
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

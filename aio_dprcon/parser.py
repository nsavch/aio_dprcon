import logging
import re

logger = logging.getLogger(__name__)


class BaseOneLineParser:
    key = b''
    started = False
    finished = True

    def __init__(self, rcon_server):
        self.rcon_server = rcon_server

    def parse(self, lines):
        if not lines:
            return lines
        if lines[0].startswith(self.key):
            try:
                self.process(lines[0][len(self.key):])
            except:
                logger.warning('Exception during parsing line %r', lines[0], exc_info=True)
            return lines[1:]
        else:
            return lines

    def process(self, data):
        raise NotImplementedError  # pragma: no cover


class BaseOneLineRegexParser:
    regex = None
    started = False
    finished = True

    def __init__(self, rcon_server):
        self.rcon_server = rcon_server

    def parse(self, lines):
        if not lines:
            return lines
        m = self.regex.match(lines[0])
        if m is None:
            return lines
        else:
            try:
                self.process(m)
            except:
                logger.warning('Exception during parsing line %r', lines[0], exc_info=True)
            return lines[1:]

    def process(self, data):
        raise NotImplementedError  # pragma: no cover


class BaseMultilineParser:
    key = b''
    is_multiline = False
    terminator = b''

    def __init__(self, rcon_server):
        self.rcon_server = rcon_server
        self.started = False
        self.finished = False
        self.received_eol = False
        self.lines = []

    def parse(self, lines):
        if not lines:
            return lines
        if self.started:
            line = lines.pop(0)
            while not line.startswith(self.terminator):
                self.lines.append(line)
                if not lines:
                    return []
                else:
                    line = lines.pop(0)
            try:
                self.process(self.lines)
            except:
                logger.warning('Exception during parsing multiline %r', self.lines, exc_info=True)
            self.finished = True
            return lines
        else:
            if lines[0].startswith(self.key):
                self.lines.append(lines.pop(0)[len(self.key):])
                self.started = True
                return self.parse(lines)
            else:
                return lines

    def process(self, data):
        raise NotImplementedError  # pragma: no cover


class CombinedParser:
    parsers = []

    def __init__(self, rcon_server, parsers=None, dump_to=None):
        self.rcon_server = rcon_server
        self.current = b''
        self.active_parser = None
        if parsers:
            self.parsers = parsers
        self.dump_to = dump_to

    def feed(self, data):
        if self.dump_to:
            self.dump_to.write(data)
        self.current += data
        self.parse()

    def parse(self):
        *lines, self.current = self.current.split(b'\n')
        if self.active_parser:
            lines = self.active_parser.parse(lines)
            if self.active_parser.finished:
                self.active_parser = None
        while lines:
            prev_len = len(lines)
            for i in self.parsers:
                parser = i(self.rcon_server)
                lines = parser.parse(lines)
                if parser.started and (not parser.finished):
                    self.active_parser = parser
                    if lines:
                        logger.error('A multi-line parser %r has not finished but left some lines %r',
                                     parser, lines)
                    else:
                        logger.debug('Waiting for more input for parser %r', parser)
            if len(lines) == prev_len:
                lines.pop(0)


class StatusItemParser(BaseOneLineRegexParser):
    regex = re.compile(rb'^(host|version|protocol|map|timing|players):\s*(.*)$')

    def process(self, data):
        key = data.group(1).decode('utf8')
        value = data.group(2).decode('utf8')
        self.rcon_server.status[key] = value


class CvarParser(BaseOneLineRegexParser):
    regex = re.compile(rb'^"(\w+)" is "([^"]*)"')

    def process(self, data):
        self.rcon_server.cvars[data.group(1).decode('utf8')] = data.group(2).decode('utf8')
        logger.debug('Set cvar %s to %r', data.group(1).decode('utf8'), data.group(2).decode('utf8'))


class AproposCvarParser(BaseOneLineRegexParser):
    regex = re.compile(rb'^cvar \^\d(\w+)\^\d is "([^"]*)"')

    def process(self, data):
        var = data.group(1).decode('utf8')
        val = data.group(2).decode('utf8')
        self.rcon_server.completions['cvar'][var] = val


class AproposAliasCommandParser(BaseOneLineRegexParser):
    regex = re.compile(rb'^(alias|command) \^\d(\w+)\^\d: (.*)')

    def process(self, data):
        type_ = data.group(1).decode('utf8')
        name = data.group(2).decode('utf8')
        description = data.group(3).decode()
        self.rcon_server.completions[type_][name] = description


class ResultsParser(BaseOneLineRegexParser):
    regex = re.compile(rb'^\d+ results$')

    def process(self, data):
        print(data.group(0))

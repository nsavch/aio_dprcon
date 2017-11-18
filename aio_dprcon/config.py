import json
import os
import re

import asyncio
import yaml

from aio_dprcon.client import RconClient
from .exceptions import InvalidConfigException


# ServerConfigItem = namedtuple('ServerConfigItem', 'name,host,port,secure,password')


class ServerConfigItem:
    fields = [
        # field_name, required, validation_regexp, type, description
        ('name', re.compile('\w{1,32}'), str, 'Server name'),
        ('host', None, str, 'Server host (domain name or IP)'),
        ('port', re.compile('\d+'), int, 'Server port'),
        ('secure', re.compile('[012]'), int, 'Rcon security mode (0, 1, 2)'),
        ('password', None, str, 'Rcon password')
    ]

    def __init__(self, **fields):
        for k, v in fields.items():
            setattr(self, k, v)

    def get_completion_cache_path(self):
        return os.path.expanduser('~/.config/aio_dprcon/completions.{}'.format(self.name))

    def update_completions(self, completions):
        path = self.get_completion_cache_path()
        with open(path, 'w') as f:
            f.write(json.dumps(completions))

    def load_completions(self):
        path = self.get_completion_cache_path()
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.loads(f.read())
        else:
            return None

    @classmethod
    def from_dict(cls, name, d):
        field_dict = {'name': name}
        for field in cls.fields[1:]:
            if field[0] not in d:
                raise InvalidConfigException('Required attribute missing: {}'.format(field[0]))
            else:
                value = str(d[field[0]])
                if field[1] and not field[1].match(value):
                    raise InvalidConfigException('Field value is invalid: {}'.format(field[0]))
                field_dict[field[0]] = field[2](value)
        return cls(**field_dict)

    @classmethod
    def from_input(cls):
        field_dict = {}
        for field in cls.fields:
            while True:
                value = input('{}: '.format(field[-1]))
                if not value:
                    print('Please enter a value')
                else:
                    if field[1] and not field[1].match(value):
                        print('Invalid value')
                    else:
                        field_dict[field[0]] = field[2](value)
                        break
        return cls(**field_dict)

    def to_dict(self):
        return dict([(field[0], getattr(self, field[0])) for field in self.fields[1:]])

    def get_client(self, loop=None):
        return RconClient(loop or asyncio.get_event_loop(),
                          self.host,
                          self.port,
                          password=self.password,
                          secure=self.secure)


class Config:
    def __init__(self):
        self.servers = {}

    @staticmethod
    def get_path():
        return os.path.expanduser('~/.config/aio_dprcon/config.yaml')

    @classmethod
    def initialize(cls):
        path = cls.get_path()
        if os.path.exists(path):
            raise InvalidConfigException('Config.initialize called, but the config already exists')
        # Why is there no mkdir -p in standard python library? :sigh:
        cur = '/'
        for d in path.split('/')[:-1]:
            cur = os.path.join(cur, d)
            if os.path.exists(cur):
                if os.path.isdir(cur):
                    continue
                else:
                    raise InvalidConfigException('{} is not directory'.format(cur))
            else:
                os.mkdir(cur)
        with open(path, 'w') as f:
            f.write(yaml.dump({'servers': {}}))
        os.chmod(path, 0o600)

    @classmethod
    def load(cls):
        path = cls.get_path()
        if not os.path.exists(path):
            cls.initialize()
        try:
            with open(path, 'r') as f:
                data = yaml.load(f.read())
            instance = cls()
            for name, server in data['servers'].items():
                instance.servers[name] = ServerConfigItem.from_dict(name, server)
            return instance
        except (IOError, OSError, KeyError):
            raise InvalidConfigException('Could not open config file: {}'.format(path))

    def save(self):
        path = self.get_path()
        contents = yaml.dump({'servers': dict([(name, server.to_dict()) for name, server in self.servers.items()])})
        try:
            with open(path, 'w') as f:
                f.write(contents)
        except (IOError, OSError, KeyboardInterrupt):
            raise InvalidConfigException('Could not write config file: {}'.format(path))

    def add_server(self, server):
        if server.name in self.servers:
            raise InvalidConfigException('Server {} already exists'.format(server.name))
        self.servers[server.name] = server

    def remove_server(self, server_name):
        if server_name not in self.servers:
            raise InvalidConfigException('Server {} does not exist'.format(server_name))
        del self.servers[server_name]

    def get_server(self, server_name):
        try:
            return self.servers[server_name]
        except KeyError:
            raise InvalidConfigException('No server {} defined'.format(server_name))

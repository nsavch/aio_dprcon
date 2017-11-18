import json
import os
import re

import yaml

from .exceptions import InvalidConfigException


# ServerConfigItem = namedtuple('ServerConfigItem', 'name,host,port,secure,password')


class ServerConfigItem:
    fields = [
        # field_name, required, validation_regexp, type, description
        ('name', True, re.compile('.{1,32}'), str, 'Server name'),
        ('host', True, None, str, 'Server host (domain name or IP)'),
        ('port', True, re.compile('\d+'), int, 'Server port'),
        ('secure', True, re.compile('[012]'), int, 'Rcon security mode (0, 1, 2)'),
        ('password', False, None, str, 'Rcon password')
    ]

    def __init__(self, **fields):
        for k, v in fields.items():
            setattr(self, k, v)
        self.validate_secure()

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

    def validate_secure(self):
        if self.secure != 0 and not self.password:
            raise InvalidConfigException('No password specified when security mode is {}'.format(self.secure))

    @classmethod
    def from_dict(cls, d):
        field_dict = {}
        for field in cls.fields:
            if field[0] not in d:
                if field[1]:
                    raise InvalidConfigException('Required attribute missing: {}'.format(field[0]))
                else:
                    field_dict[field[0]] = ''
            else:
                value = str(d[field[0]])
                if field[2] and not field[2].match(value):
                    raise InvalidConfigException('Field value is invalid: {}'.format(field[0]))
                field_dict[field[0]] = field[3](value)
        return cls(**field_dict)

    @classmethod
    def from_input(cls):
        field_dict = {}
        for field in cls.fields:
            while True:
                value = input('{}: '.format(field[-1]))
                if not value:
                    if field[1]:
                        print('Please enter a value')
                        continue
                    else:
                        field_dict[field[0]] = ''
                        break
                else:
                    if field[2] and not field[2].match(value):
                        print('Invalid value')
                        continue
                    else:
                        field_dict[field[0]] = field[3](value)
                        break
        return cls(**field_dict)

    def to_dict(self):
        return dict([(field[0], getattr(self, field[0])) for field in self.fields])


class Config:
    def __init__(self):
        self.servers = []

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
            f.write(yaml.dump({'servers': []}))
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
            instance.servers = []
            for server in data['servers']:
                instance.servers.append(ServerConfigItem.from_dict(server))
            return instance
        except (IOError, OSError, KeyError):
            raise InvalidConfigException('Could not open config file: {}'.format(path))

    def save(self):
        path = self.get_path()
        contents = yaml.dump({'servers': [i.to_dict() for i in self.servers]})
        try:
            with open(path, 'w') as f:
                f.write(contents)
        except (IOError, OSError, KeyboardInterrupt):
            raise InvalidConfigException('Could not write config file: {}'.format(path))

    def add_server(self, server):
        for i in self.servers:
            if i.name == server.name:
                raise InvalidConfigException('Server {} already exists'.format(server.name))
        self.servers.append(server)

    def get_server(self, server_name):
        for i in self.servers:
            if i.name == server_name:
                return i
        raise InvalidConfigException('No server {} defined'.format(server_name))

class RconException(Exception):
    pass


class RconCommandFailed(RconException):
    pass


class RconCommandTimeout(RconCommandFailed):
    pass


class RconCommandRetryNumberExceeded(RconCommandFailed):
    pass

import pytest
from click.testing import CliRunner


@pytest.fixture()
def cli_runner():
    """
    Provides click runner object
    """
    return CliRunner()

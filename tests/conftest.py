import uuid
from types import SimpleNamespace

import pytest
from yarl import URL
from sqlalchemy_utils import drop_database, create_database

from src.settings import POSTGRES_URI, make_alembic_config


@pytest.fixture()
def postgres():
    """
    Create tmp postgres instance
    """
    tmp_name = ".".join([uuid.uuid4().hex, "pytest"])
    tmp_url = str(URL(POSTGRES_URI).with_path(tmp_name))
    create_database(tmp_url)

    try:
        yield tmp_url
    finally:
        drop_database(tmp_url)


@pytest.fixture()
def alembic_config(postgres):
    """
    Provides Python object, representing alembic.ini file.
    """
    cmd_options = SimpleNamespace(
        config="alembic.ini", name="alembic", pg_url=postgres, raiseerr=False, x=None
    )
    return make_alembic_config(cmd_options)

import datetime
from uuid import uuid4

from itstart_core_api import schemas
from itstart_domain import PublicationType, TagCategory, ParserType, AdminRole


def test_publication_read_from_kwargs():
    pub = schemas.PublicationRead(
        id=uuid4(),
        title="T",
        description="D",
        type=PublicationType.job,
        company="C",
        url="https://ex",
        created_at=datetime.datetime.utcnow(),
        vacancy_created_at=datetime.datetime.utcnow(),
        is_edited=False,
        is_declined=False,
    )
    assert pub.title == "T"
    assert pub.tags == []


def test_parser_read():
    pr = schemas.ParserRead(
        id=uuid4(),
        source_name="s",
        executable_file_path="/path",
        type=ParserType.api_client,
        parsing_interval=10,
        parsing_start_time=datetime.datetime.utcnow(),
        is_active=True,
    )
    assert pr.type == ParserType.api_client


def test_admin_user_read():
    au = schemas.AdminUserRead(
        id=uuid4(),
        username="u",
        role=AdminRole.admin,
        is_active=True,
        created_at=datetime.datetime.utcnow(),
    )
    assert au.username == "u"

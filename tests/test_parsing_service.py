import datetime
import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from itstart_core_api import models
from itstart_core_api.config import Settings
from itstart_core_api.parsing_service import run_parsers_once


@pytest.mark.asyncio
async def test_run_parsers_once_ingests_and_tags(tmp_path, monkeypatch):
    db_path = tmp_path / "parsers.db"
    monkeypatch.setenv("POSTGRES_DSN", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("SECRET_KEY", "secret")
    settings = Settings()

    engine = create_async_engine(settings.database_url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    script_path = tmp_path / "fake_parser.py"
    now_iso = datetime.datetime.utcnow().isoformat()
    payload = [
        {
            "title": "React Developer",
            "company": "ACME",
            "description": "Work on React stack",
            "url": "https://example.com/jobs/1",
            "type": "job",
            "created_at": now_iso,
            "vacancy_created_at": now_iso,
        },
        {
            "title": "React Developer duplicate",
            "company": "ACME",
            "description": "React role duplicate",
            "url": "https://example.com/jobs/1",
            "type": "job",
            "created_at": now_iso,
            "vacancy_created_at": now_iso,
        },
    ]

    script_path.write_text(
        "import json, sys\n" f"data = {json.dumps(payload)}\n" "json.dump(data, sys.stdout)\n"
    )

    async with Session() as session:
        tag = models.Tag(name="react", category=models.TagCategory.technology)
        session.add(tag)
        parser = models.Parser(
            source_name="fake",
            executable_file_path=f"python {script_path}",
            type=models.ParserType.website_parser,
            parsing_interval=60,
            parsing_start_time=datetime.datetime.utcnow() - datetime.timedelta(minutes=5),
            is_active=True,
        )
        session.add(parser)
        await session.commit()

    await run_parsers_once(Session, settings)

    async with Session() as session:
        pubs = list((await session.execute(select(models.Publication))).scalars())
        assert len(pubs) == 1
        pub = pubs[0]
        assert pub.company == "ACME"

        tags = list((await session.execute(select(models.PublicationTag))).scalars())
        assert len(tags) == 1

        results = list((await session.execute(select(models.ParsingResult))).scalars())
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].received_amount == 2

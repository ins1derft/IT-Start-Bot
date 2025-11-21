from uuid import uuid4

import pytest
from itstart_core_api import models
from itstart_core_api.repositories import AdminAuditRepository
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.mark.asyncio
async def test_admin_audit_log():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        repo = AdminAuditRepository(session)
        admin_id = uuid4()
        repo.log(
            admin_id=admin_id,
            action="test",
            target_type="admin_user",
            target_id=uuid4(),
            details="demo",
        )
        await session.commit()
        rows = (await session.execute(models.AdminAuditLog.__table__.select())).fetchall()
        assert len(rows) == 1

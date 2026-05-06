import asyncio
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .db import init_db, async_session
from .models import Port, Ship, CallRequest, RuleSet

async def seed():
    await init_db()
    async for session in async_session():
        await seed_once(session)

async def seed_once(session: AsyncSession):
    existing_ports = (await session.execute(select(Port))).scalars().all()
    if not existing_ports:
        session.add_all([
            Port(name="Kotor", daily_pax_capacity=9000, max_berths=3, max_ship_length_m=330, max_draft_m=8.5),
            Port(name="Bar", daily_pax_capacity=12000, max_berths=4, max_ship_length_m=360, max_draft_m=10.5),
        ])
    if not (await session.execute(select(RuleSet))).scalars().first():
        session.add(RuleSet())

    today = date.today()
    ships = []
    for i in range(1, 11):
        ships.append(Ship(name=f"Ship {i}", length_m=250 + (i*5), draft_m=7 + (i*0.1), pax_capacity=1500 + i*200))
    session.add_all(ships)
    await session.flush()

    requests = []
    for i, s in enumerate(ships, start=1):
        pax = 2000 + (i*150)
        requests.append(CallRequest(
            ship_id=s.id,
            pax_expected=pax,
            eta_earliest=today + timedelta(days=i),
            eta_latest=today + timedelta(days=i+2),
            preferred_port=None,
            priority=0
        ))
    session.add_all(requests)
    await session.commit()

if __name__ == "__main__":
    asyncio.run(seed())

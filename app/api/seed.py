import asyncio
from datetime import date
from sqlalchemy import select
from .db import async_session, init_db
from .models import Port, Ship, CruiseRequest, RuleSet


async def seed():
    # osiguraj da tabele postoje
    await init_db()

    async with async_session() as db:
        # ----- RULESET -----
        result = await db.execute(select(RuleSet))
        existing_ruleset = result.scalars().first()
        if not existing_ruleset:
            default_rules = RuleSet(
                kotor_target_share=0.85,
                big_ship_length_threshold=1500.0,
                big_ship_pax_threshold=3000,
                bar_big_ship_mandatory=True,
                max_calls_per_day_per_port=0,
            )
            db.add(default_rules)

        # ----- PORTS -----
        result = await db.execute(select(Port))
        if not result.scalars().first():
            ports = [
                Port(
                    name="Kotor",
                    max_berths=3,
                    daily_pax_capacity=9000,
                    max_ship_length_m=330.0,
                    max_draft_m=8.5,
                ),
                Port(
                    name="Bar",
                    max_berths=4,
                    daily_pax_capacity=12000,
                    max_ship_length_m=360.0,
                    max_draft_m=10.5,
                ),
            ]
            db.add_all(ports)

        # ----- SHIPS -----
        result = await db.execute(select(Ship))
        if not result.scalars().first():
            ships = [
                Ship(name="Ship 1", length_m=268.0, draft_m=7.7, pax_capacity=2100),
                Ship(name="Ship 2", length_m=276.0, draft_m=7.9, pax_capacity=2400),
                Ship(name="Ship 3", length_m=284.0, draft_m=8.1, pax_capacity=2700),
                Ship(name="Ship 4", length_m=292.0, draft_m=8.3, pax_capacity=3000),
                Ship(name="Ship 5", length_m=300.0, draft_m=8.5, pax_capacity=3300),
            ]
            db.add_all(ships)

        # ----- REQUESTS -----
        result = await db.execute(select(CruiseRequest))
        if not result.scalars().first():
            reqs = [
                CruiseRequest(
                    ship_id=1,
                    pax_expected=2500,
                    eta_earliest=date(2025, 5, 1),
                    eta_latest=date(2025, 5, 3),
                    preferred_port=None,
                    priority=1,
                ),
                CruiseRequest(
                    ship_id=2,
                    pax_expected=2800,
                    eta_earliest=date(2025, 5, 2),
                    eta_latest=date(2025, 5, 4),
                    preferred_port=None,
                    priority=1,
                ),
                CruiseRequest(
                    ship_id=3,
                    pax_expected=3100,
                    eta_earliest=date(2025, 5, 3),
                    eta_latest=date(2025, 5, 5),
                    preferred_port=None,
                    priority=1,
                ),
                CruiseRequest(
                    ship_id=4,
                    pax_expected=3400,
                    eta_earliest=date(2025, 5, 4),
                    eta_latest=date(2025, 5, 6),
                    preferred_port=None,
                    priority=1,
                ),
                CruiseRequest(
                    ship_id=5,
                    pax_expected=3700,
                    eta_earliest=date(2025, 5, 5),
                    eta_latest=date(2025, 5, 7),
                    preferred_port=None,
                    priority=1,
                ),
            ]
            db.add_all(reqs)

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())

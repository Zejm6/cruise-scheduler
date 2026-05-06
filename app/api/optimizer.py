from datetime import timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import CruiseRequest, Port
from .schemas import OptimizeRequest, OptimizeResponse, ScheduleEntry


async def solve_schedule_ilp(
    db: AsyncSession,
    payload: OptimizeRequest,
) -> OptimizeResponse:
    """
    Jednostavan 'fake' optimizator:
    - uzme sve zahtjeve iz baze
    - uzme sve luke
    - napravi listu dana u zadatom opsegu
    - kružno rasporedi zahtjeve po danima i lukama
    - vrati i dummy KPIs da zadovolji schema-u
    """

    # payload.date_range je objekat sa .start i .end
    start = payload.date_range.start
    end = payload.date_range.end

    # Lista svih dana u opsegu [start, end]
    days: List = []
    d = start
    while d <= end:
        days.append(d)
        d += timedelta(days=1)

    # Učitamo sve zahtjeve i luke iz baze
    result = await db.execute(select(CruiseRequest))
    requests = result.scalars().all()

    result = await db.execute(select(Port))
    ports = result.scalars().all()

    # Ako nema podataka, vrati prazan raspored + dummy KPIs
    if not requests or not ports or not days:
        return OptimizeResponse(
            schedule=[],
            kpis={
                "kotor_share": None,
                "max_daily_pax": None,
                "violations": 0,
            },
        )

    schedule_entries: List[ScheduleEntry] = []

    port_index = 0
    day_index = 0

    for req in requests:
        day = days[day_index]
        port = ports[port_index]

        # VAŽNO:
        # ScheduleEntry u schemama/frontendu očekuje:
        #   request_id: int
        #   port: str (ime luke)
        #   call_date: date
        schedule_entries.append(
            ScheduleEntry(
                request_id=req.id,
                port=port.name,
                call_date=day,
            )
        )

        # kružno pomjeranje po danima i lukama
        day_index = (day_index + 1) % len(days)
        port_index = (port_index + 1) % len(ports)

    # Dummy KPIs – samo da API bude konzistentan sa frontendom/schemama
    kpis = {
        "kotor_share": None,   # ovdje bi išao pravi proračun
        "max_daily_pax": None, # ovdje max pax po danu
        "violations": 0,       # broj prekršenih ograničenja
    }

    return OptimizeResponse(
        schedule=schedule_entries,
        kpis=kpis,
    )

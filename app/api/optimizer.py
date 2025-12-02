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
    """

    # payload.date_range je DateRange objekat (nije dict!)
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

    # Ako nema podataka, vrati prazan raspored
    if not requests or not ports or not days:
        return OptimizeResponse(schedule=[])

    schedule_entries: List[ScheduleEntry] = []

    port_index = 0
    day_index = 0

    for req in requests:
        day = days[day_index]
        port = ports[port_index]

        schedule_entries.append(
            ScheduleEntry(
                request_id=req.id,
                port_id=port.id,
                date=day,
            )
        )

        # kružno pomjeranje po danima i lukama
        day_index = (day_index + 1) % len(days)
        port_index = (port_index + 1) % len(ports)

    return OptimizeResponse(schedule=schedule_entries)

from datetime import timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Port, CallRequest, Schedule
from .schemas import OptimizeRequest, OptimizeResponse, ScheduledItem, KPIs

async def solve_schedule_stub(session: AsyncSession, payload: OptimizeRequest) -> OptimizeResponse:
    ports = {p.name: p for p in (await session.execute(select(Port))).scalars().all()}
    if "Kotor" not in ports or "Bar" not in ports:
        raise RuntimeError("Ports 'Kotor' and 'Bar' must exist; run seed.")
    calls = (await session.execute(select(CallRequest))).scalars().all()

    out: list[ScheduledItem] = []
    cur_day = payload.date_range.start
    for r in calls:
        big = (r.pax_expected or 0) >= 3500
        port = "Bar" if big else "Kotor"
        d = r.eta_earliest if cur_day < r.eta_earliest else cur_day
        if d > r.eta_latest:
            d = r.eta_latest
        out.append(ScheduledItem(request_id=r.id, port=port, call_date=d))
        cur_day = d + timedelta(days=1)

    return OptimizeResponse(
        schedule=out,
        kpis=KPIs(kotor_share=None, max_daily_pax=None, violations=0)
    )

async def persist_schedule(session: AsyncSession, items: list[ScheduledItem]) -> None:
    # mapiraj nazive luka u id
    ports = {p.name: p.id for p in (await session.execute(select(Port))).scalars().all()}
    for it in items:
        port_id = ports[it.port]
        # upsert po request_id
        existing = (await session.execute(
            select(Schedule).where(Schedule.request_id == it.request_id)
        )).scalars().first()
        if existing:
            existing.port_id = port_id
            existing.call_date = it.call_date
        else:
            session.add(Schedule(request_id=it.request_id, port_id=port_id, call_date=it.call_date))
    await session.commit()

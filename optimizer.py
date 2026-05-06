from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Port, CallRequest
from .schemas import OptimizeRequest, OptimizeResponse, ScheduledItem, KPIs

async def solve_schedule_stub(session: AsyncSession, payload: OptimizeRequest) -> OptimizeResponse:
    ports = {p.name: p for p in (await session.execute(select(Port))).scalars().all()}
    if not ports:
        raise RuntimeError("Seed ports first: Kotor and Bar")

    calls = (await session.execute(select(CallRequest))).scalars().all()
    out: list[ScheduledItem] = []
    cur_day = payload.date_range.start

    for r in calls:
        big = r.pax_expected >= 3500
        port = "Bar" if big else "Kotor"
        d = max(cur_day, r.eta_earliest)
        if d > r.eta_latest:
            d = r.eta_latest
        out.append(ScheduledItem(request_id=r.id, port=port, call_date=d))
        cur_day = d + timedelta(days=1)

    return OptimizeResponse(schedule=out, kpis=KPIs(kotor_share=None, max_daily_pax=None, violations=0))
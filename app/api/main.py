from fastapi import FastAPI, Depends, Query
from datetime import date
from dotenv import load_dotenv
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from .db import init_db, async_session
from .schemas import OptimizeRequest, OptimizeResponse, ScheduledItem
from .optimizer import solve_schedule_stub, persist_schedule
from .models import Schedule, Port

load_dotenv()
app = FastAPI(title="Cruise Scheduler API", version="0.2.0")

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/optimize", response_model=OptimizeResponse)
async def optimize(payload: OptimizeRequest, session: AsyncSession = Depends(async_session)):
    result = await solve_schedule_stub(session, payload)
    return result

@app.post("/optimize-and-save", response_model=OptimizeResponse)
async def optimize_and_save(payload: OptimizeRequest, session: AsyncSession = Depends(async_session)):
    result = await solve_schedule_stub(session, payload)
    await persist_schedule(session, result.schedule)
    return result

@app.get("/schedule", response_model=list[ScheduledItem])
async def get_schedule(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    port: str | None = None,
    session: AsyncSession = Depends(async_session),
):
    stmt = (
        select(Schedule.request_id, Schedule.call_date, Port.name)
        .join(Port, Port.id == Schedule.port_id)
    )
    conds = []
    if from_date:
        conds.append(Schedule.call_date >= from_date)
    if to_date:
        conds.append(Schedule.call_date <= to_date)
    if port:
        conds.append(Port.name == port)
    if conds:
        stmt = stmt.where(and_(*conds))

    rows = (await session.execute(stmt)).all()
    return [ScheduledItem(request_id=r[0], call_date=r[1], port=r[2]) for r in rows]

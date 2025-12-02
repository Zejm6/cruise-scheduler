from typing import List

from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from .db import get_session, init_db
from .models import Port, Ship, CruiseRequest, RuleSet
from .schemas import (
    PortCreate,
    PortRead,
    ShipCreate,
    ShipRead,
    ShipUpdate,
    CruiseRequestRead,
    OptimizeRequest,
    OptimizeResponse,
    RuleSetRead,
    RuleSetUpdate,
)
from .optimizer import solve_schedule_ilp


app = FastAPI(title="Cruise Scheduler API")

# CORS – za tvoj frontend na localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    # kreira tabele ako ne postoje
    await init_db()


@app.get("/health")
async def health():
    return {"ok": True}


# ---------------------------
# PORTS
# ---------------------------

@app.get("/ports", response_model=List[PortRead])
async def list_ports(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Port))
    return result.scalars().all()


@app.post("/ports", response_model=PortRead)
async def create_port(payload: PortCreate, session: AsyncSession = Depends(get_session)):
    port = Port(
        name=payload.name,
        max_berths=payload.max_berths,
        daily_pax_capacity=payload.daily_pax_capacity,
        max_ship_length_m=payload.max_ship_length_m,
        max_draft_m=payload.max_draft_m,
    )
    session.add(port)
    await session.commit()
    await session.refresh(port)
    return port


# ---------------------------
# SHIPS
# ---------------------------

@app.get("/ships", response_model=List[ShipRead])
async def list_ships(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Ship))
    return result.scalars().all()


@app.post("/ships", response_model=ShipRead)
async def create_ship(payload: ShipCreate, session: AsyncSession = Depends(get_session)):
    ship = Ship(
        name=payload.name,
        length_m=payload.length_m,
        draft_m=payload.draft_m,
        pax_capacity=payload.pax_capacity,
    )
    session.add(ship)
    await session.commit()
    await session.refresh(ship)
    return ship


@app.patch("/ships/{ship_id}", response_model=ShipRead)
async def update_ship(
    ship_id: int,
    payload: ShipUpdate,
    session: AsyncSession = Depends(get_session),
):
    ship = await session.get(Ship, ship_id)
    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(ship, field, value)

    await session.commit()
    await session.refresh(ship)
    return ship


@app.delete("/ships/{ship_id}", status_code=204)
async def delete_ship(
    ship_id: int,
    session: AsyncSession = Depends(get_session),
):
    # prvo izbriši sve zahtjeve za ovaj brod
    await session.execute(
        delete(CruiseRequest).where(CruiseRequest.ship_id == ship_id)
    )

    ship = await session.get(Ship, ship_id)
    if not ship:
        # ako nema broda, vrati 404
        raise HTTPException(status_code=404, detail="Ship not found")

    await session.delete(ship)
    await session.commit()

    # 204 No Content
    return Response(status_code=204)


# ---------------------------
# CRUISE REQUESTS (read-only za sada)
# ---------------------------

@app.get("/requests", response_model=List[CruiseRequestRead])
async def list_requests(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(CruiseRequest))
    return result.scalars().all()


# ---------------------------
# RULESET
# ---------------------------

@app.get("/rules", response_model=RuleSetRead)
async def get_rules(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(RuleSet))
    ruleset = result.scalars().first()

    if not ruleset:
        # ako nema zapisa, kreiraj default
        ruleset = RuleSet(
            allow_oversize_ships=True,
            allow_draft_exceed=False,
            enforce_daily_pax_capacity=True,
            allow_multiple_ships_per_berth=False,
        )
        session.add(ruleset)
        await session.commit()
        await session.refresh(ruleset)

    return ruleset


@app.patch("/rules", response_model=RuleSetRead)
async def update_rules(
    payload: RuleSetUpdate,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(RuleSet))
    ruleset = result.scalars().first()

    if not ruleset:
        raise HTTPException(status_code=404, detail="Ruleset not found")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(ruleset, field, value)

    await session.commit()
    await session.refresh(ruleset)
    return ruleset


# ---------------------------
# OPTIMIZER
# ---------------------------

@app.post("/optimize-ilp", response_model=OptimizeResponse)
async def optimize(
    payload: OptimizeRequest,
    session: AsyncSession = Depends(get_session),
):
    return await solve_schedule_ilp(session, payload)

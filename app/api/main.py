from datetime import date
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_session, init_db
from .models import Port, Ship, CruiseRequest, RuleSet
from .schemas import OptimizeRequest, OptimizeResponse
from .optimizer import solve_schedule_ilp


app = FastAPI(title="Smart Port API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
	"https://main.dimklaeoxje9x.amplifyapp.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PortCreate(BaseModel):
    name: str
    max_berths: int
    daily_pax_capacity: int
    max_ship_length_m: float
    max_draft_m: float


class PortUpdate(BaseModel):
    name: Optional[str] = None
    max_berths: Optional[int] = None
    daily_pax_capacity: Optional[int] = None
    max_ship_length_m: Optional[float] = None
    max_draft_m: Optional[float] = None


class PortRead(PortCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ShipCreate(BaseModel):
    name: str
    length_m: float
    draft_m: float
    pax_capacity: int


class ShipUpdate(BaseModel):
    name: Optional[str] = None
    length_m: Optional[float] = None
    draft_m: Optional[float] = None
    pax_capacity: Optional[int] = None


class ShipRead(ShipCreate):
    id: int
    port_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class CruiseRequestCreate(BaseModel):
    ship_id: int
    pax_expected: int
    eta_earliest: date
    eta_latest: date
    preferred_port: Optional[str] = None
    priority: int = 0


class CruiseRequestUpdate(BaseModel):
    ship_id: Optional[int] = None
    pax_expected: Optional[int] = None
    eta_earliest: Optional[date] = None
    eta_latest: Optional[date] = None
    preferred_port: Optional[str] = None
    priority: Optional[int] = None


class CruiseRequestRead(CruiseRequestCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class RuleSetRead(BaseModel):
    id: int
    kotor_target_share: float
    big_ship_length_threshold: float
    big_ship_pax_threshold: int
    bar_big_ship_mandatory: bool
    max_calls_per_day_per_port: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class RuleSetUpdate(BaseModel):
    kotor_target_share: Optional[float] = None
    big_ship_length_threshold: Optional[float] = None
    big_ship_pax_threshold: Optional[int] = None
    bar_big_ship_mandatory: Optional[bool] = None
    max_calls_per_day_per_port: Optional[int] = None


@app.on_event("startup")
async def on_startup():
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


@app.patch("/ports/{port_id}", response_model=PortRead)
async def update_port(
    port_id: int,
    payload: PortUpdate,
    session: AsyncSession = Depends(get_session),
):
    port = await session.get(Port, port_id)
    if not port:
        raise HTTPException(status_code=404, detail="Port not found")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(port, field, value)

    await session.commit()
    await session.refresh(port)
    return port


@app.delete("/ports/{port_id}", status_code=204)
async def delete_port(
    port_id: int,
    session: AsyncSession = Depends(get_session),
):
    port = await session.get(Port, port_id)
    if not port:
        raise HTTPException(status_code=404, detail="Port not found")

    await session.delete(port)
    await session.commit()
    return Response(status_code=204)


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
    await session.execute(
        delete(CruiseRequest).where(CruiseRequest.ship_id == ship_id)
    )

    ship = await session.get(Ship, ship_id)
    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    await session.delete(ship)
    await session.commit()
    return Response(status_code=204)


# ---------------------------
# REQUESTS
# ---------------------------

@app.get("/requests", response_model=List[CruiseRequestRead])
async def list_requests(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(CruiseRequest))
    return result.scalars().all()


@app.post("/requests", response_model=CruiseRequestRead)
async def create_request(
    payload: CruiseRequestCreate,
    session: AsyncSession = Depends(get_session),
):
    ship = await session.get(Ship, payload.ship_id)
    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    request = CruiseRequest(
        ship_id=payload.ship_id,
        pax_expected=payload.pax_expected,
        eta_earliest=payload.eta_earliest,
        eta_latest=payload.eta_latest,
        preferred_port=payload.preferred_port,
        priority=payload.priority,
    )

    session.add(request)
    await session.commit()
    await session.refresh(request)
    return request


@app.patch("/requests/{request_id}", response_model=CruiseRequestRead)
async def update_request(
    request_id: int,
    payload: CruiseRequestUpdate,
    session: AsyncSession = Depends(get_session),
):
    request = await session.get(CruiseRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    data = payload.model_dump(exclude_unset=True)

    if "ship_id" in data:
        ship = await session.get(Ship, data["ship_id"])
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")

    for field, value in data.items():
        setattr(request, field, value)

    await session.commit()
    await session.refresh(request)
    return request


@app.delete("/requests/{request_id}", status_code=204)
async def delete_request(
    request_id: int,
    session: AsyncSession = Depends(get_session),
):
    request = await session.get(CruiseRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    await session.delete(request)
    await session.commit()
    return Response(status_code=204)


# ---------------------------
# RULES
# ---------------------------

@app.get("/rules", response_model=RuleSetRead)
async def get_rules(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(RuleSet))
    ruleset = result.scalars().first()

    if not ruleset:
        ruleset = RuleSet(
            kotor_target_share=0.85,
            big_ship_length_threshold=300.0,
            big_ship_pax_threshold=3000,
            bar_big_ship_mandatory=True,
            max_calls_per_day_per_port=3,
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
        ruleset = RuleSet(
            kotor_target_share=0.85,
            big_ship_length_threshold=300.0,
            big_ship_pax_threshold=3000,
            bar_big_ship_mandatory=True,
            max_calls_per_day_per_port=3,
        )
        session.add(ruleset)
        await session.commit()
        await session.refresh(ruleset)

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

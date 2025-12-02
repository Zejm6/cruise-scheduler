from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .db import get_session
from .models import Port, Ship, CruiseRequest, RuleSet
from .schemas import (
    PortCreate, Port as PortSchema,
    ShipCreate, Ship as ShipSchema,
    CruiseRequestCreate, CruiseRequest as CruiseRequestSchema,
    RuleSetCreate, RuleSet as RuleSetSchema,
    OptimizeRequest, OptimizeResponse,
)
from .optimizer import solve_schedule_ilp

router = APIRouter()

@router.get("/ports", response_model=list[PortSchema])
async def get_ports(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Port))
    return result.scalars().all()

@router.post("/ports", response_model=PortSchema)
async def create_port(payload: PortCreate, session: AsyncSession = Depends(get_session)):
    obj = Port(**payload.dict())
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj

@router.get("/ships", response_model=list[ShipSchema])
async def get_ships(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Ship))
    return result.scalars().all()

@router.get("/requests", response_model=list[CruiseRequestSchema])
async def get_requests(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(CruiseRequest))
    return result.scalars().all()

@router.post("/requests", response_model=CruiseRequestSchema)
async def create_request(payload: CruiseRequestCreate, session: AsyncSession = Depends(get_session)):
    obj = CruiseRequest(**payload.dict())
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj

@router.post("/optimize-ilp", response_model=OptimizeResponse)
async def optimize(payload: OptimizeRequest, session: AsyncSession = Depends(get_session)):
    return await solve_schedule_ilp(session, payload)

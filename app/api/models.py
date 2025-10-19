from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Text, Numeric, Date, ForeignKey, Boolean
from .db import Base

class Port(Base):
    __tablename__ = "port"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True)
    max_berths: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_pax_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_ship_length_m: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    max_draft_m: Mapped[float | None] = mapped_column(Numeric, nullable=True)

class Ship(Base):
    __tablename__ = "ship"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    length_m: Mapped[float] = mapped_column(Numeric)
    draft_m: Mapped[float] = mapped_column(Numeric)
    pax_capacity: Mapped[int] = mapped_column(Integer)

class CallRequest(Base):
    __tablename__ = "call_request"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ship_id: Mapped[int] = mapped_column(ForeignKey("ship.id", ondelete="CASCADE"))
    pax_expected: Mapped[int] = mapped_column(Integer)
    eta_earliest: Mapped[Date] = mapped_column(Date)
    eta_latest: Mapped[Date] = mapped_column(Date)
    preferred_port: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)

class RuleSet(Base):
    __tablename__ = "ruleset"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kotor_target_share: Mapped[float] = mapped_column(Numeric, default=0.70)
    big_ship_length_threshold: Mapped[float] = mapped_column(Numeric, default=300)
    big_ship_pax_threshold: Mapped[int] = mapped_column(Integer, default=3500)
    bar_big_ship_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    max_calls_per_day_per_port: Mapped[int | None] = mapped_column(Integer, nullable=True)

class Schedule(Base):
    __tablename__ = "schedule"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("call_request.id", ondelete="CASCADE"), unique=True)
    port_id: Mapped[int] = mapped_column(ForeignKey("port.id"))
    call_date: Mapped[Date] = mapped_column(Date)

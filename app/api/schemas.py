from datetime import date
from pydantic import BaseModel


# ----------------- SHIPS -----------------


class ShipBase(BaseModel):
    name: str
    length_m: float
    draft_m: float
    pax_capacity: int


class ShipCreate(ShipBase):
    pass


class ShipUpdate(BaseModel):
    name: str | None = None
    length_m: float | None = None
    draft_m: float | None = None
    pax_capacity: int | None = None


class ShipRead(ShipBase):
    id: int
    port_id: int | None = None

    class Config:
        from_attributes = True


# ----------------- PORTS -----------------


class PortBase(BaseModel):
    name: str
    max_berths: int
    daily_pax_capacity: int
    max_ship_length_m: float
    max_draft_m: float


class PortCreate(PortBase):
    pass


class PortUpdate(BaseModel):
    name: str | None = None
    max_berths: int | None = None
    daily_pax_capacity: int | None = None
    max_ship_length_m: float | None = None
    max_draft_m: float | None = None


class PortRead(PortBase):
    id: int

    class Config:
        from_attributes = True


# ----------------- CRUISE REQUESTS -----------------


class CruiseRequestBase(BaseModel):
    ship_id: int
    pax_expected: int
    eta_earliest: date
    eta_latest: date
    preferred_port: str | None = None
    priority: int = 0


class CruiseRequestCreate(CruiseRequestBase):
    pass


class CruiseRequestUpdate(BaseModel):
    ship_id: int | None = None
    pax_expected: int | None = None
    eta_earliest: date | None = None
    eta_latest: date | None = None
    preferred_port: str | None = None
    priority: int | None = None


class CruiseRequestRead(CruiseRequestBase):
    id: int

    class Config:
        from_attributes = True


# ----------------- RULE SET -----------------
# Mora match-ovati app.api.models.RuleSet


class RuleSetBase(BaseModel):
    kotor_target_share: float
    big_ship_length_threshold: float
    big_ship_pax_threshold: int
    bar_big_ship_mandatory: bool
    max_calls_per_day_per_port: int | None = None


class RuleSetRead(RuleSetBase):
    id: int

    class Config:
        from_attributes = True


class RuleSetUpdate(BaseModel):
    kotor_target_share: float
    big_ship_length_threshold: float
    big_ship_pax_threshold: int
    bar_big_ship_mandatory: bool
    max_calls_per_day_per_port: int | None = None


# ----------------- OPTIMIZE / ILP -----------------


class DateRange(BaseModel):
    start: date
    end: date


class OptimizeRequest(BaseModel):
    date_range: DateRange
    ruleset_id: int


class ScheduleEntry(BaseModel):
    request_id: int
    port: str
    call_date: date


class KPIs(BaseModel):
    kotor_share: float | None = None
    max_daily_pax: int | None = None
    violations: int


class OptimizeResponse(BaseModel):
    schedule: list[ScheduleEntry]
    kpis: KPIs

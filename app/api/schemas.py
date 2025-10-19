from pydantic import BaseModel
from datetime import date

class DateRange(BaseModel):
    start: date
    end: date

class OptimizeRequest(BaseModel):
    date_range: DateRange
    ruleset_id: int | None = None

class ScheduledItem(BaseModel):
    request_id: int
    port: str
    call_date: date

class KPIs(BaseModel):
    kotor_share: float | None = None
    max_daily_pax: int | None = None
    violations: int | None = None

class OptimizeResponse(BaseModel):
    schedule: list[ScheduledItem]
    kpis: KPIs

from fastapi import FastAPI, Depends
from dotenv import load_dotenv
from .db import init_db, async_session
from .schemas import OptimizeRequest, OptimizeResponse
from .optimizer import solve_schedule_stub

load_dotenv()
app = FastAPI(title="Cruise Scheduler API", version="0.1.0")

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/optimize", response_model=OptimizeResponse)
async def optimize(payload: OptimizeRequest, session=Depends(async_session)):
    result = await solve_schedule_stub(session, payload)
    return result


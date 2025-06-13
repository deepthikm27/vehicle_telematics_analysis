from fastapi import FastAPI
import asyncio
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from api.routers import router
from api.simulator import data_simulator_task

app = FastAPI(
    title="Real-Time Vehicle Telemetry API",
    description="A FastAPI application to simulate and serve real-time vehicle telemetry data.",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    """
    FastAPI startup event handler.
    Starts the data simulator task in the background.
    """
    asyncio.create_task(data_simulator_task())

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)


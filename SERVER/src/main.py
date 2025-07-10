from fastapi import FastAPI
from .database.core import engine, Base
from .entities.users import User
from .api import register_router
from .logging import configure_logging, LogLevels
from contextlib import asynccontextmanager
from .graph import Agent
from fastapi.middleware.cors import CORSMiddleware

configure_logging(LogLevels.info)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the graph before api starts
    app.state.graph_app = Agent.graph_builder()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type"],
)

"""
For creating tables, uncomment when not needed
"""
# Base.metadata.create_all(bind=engine)

register_router(app)
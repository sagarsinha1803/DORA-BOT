from fastapi import FastAPI
from src.agent.controller import router as agent_router
from src.users.controller import router as user_router
from src.auth.controller import router as auth_router

def register_router(app: FastAPI):
    app.include_router(agent_router)
    app.include_router(user_router)
    app.include_router(auth_router)
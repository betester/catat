
from fastapi import FastAPI
from global_state import lifespan

from router import auth_router

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)


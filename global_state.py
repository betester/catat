from dataclasses import dataclass
from fastapi import FastAPI

from contextlib import asynccontextmanager

from sqlalchemy.engine import Engine
from conf import AppConfig, get_config
from db import init_db

@dataclass
class AppState:
    app_onfig: AppConfig | None = None
    db_engine: Engine | None = None

app_state = AppState()

@asynccontextmanager
async def lifespan(_: FastAPI):
    config: AppConfig = get_config()
    db_engine = init_db(config.db_config, config.environment)

    app_state.app_onfig = config
    app_state.db_engine = db_engine

    yield

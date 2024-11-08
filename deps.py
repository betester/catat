
from typing import Annotated
from conf import AppConfig
from global_state import app_state
from sqlmodel import Session

from fastapi import Depends

def get_db():
    assert app_state.db_engine != None, "App state should have been initialized during run"
    with Session(app_state.db_engine) as db:
        yield db

def get_app_config():
    assert app_state.app_onfig != None, "App state should have been initialized during run"
    yield app_state.app_onfig

DbDep = Annotated[Session, Depends(get_db)] 
AppConfigDep = Annotated[AppConfig, Depends(get_app_config)] 

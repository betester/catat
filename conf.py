
from enum import StrEnum
from os import environ
from typing import Any
from pydantic import BaseModel

from dataclasses import dataclass

class GoogleConfig(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str

class DbConfig(BaseModel):
    db_url: str
    connect_args: dict[str, Any] = {}

class Environment(StrEnum):
    Local = "Local"
    Prod = "Prod"

@dataclass
class AppConfig:
    db_config: DbConfig
    google_config: GoogleConfig
    environment: Environment



def get_config() -> AppConfig:
    environment = Environment(environ.get("ENVIRONMENT"))

    if environment == Environment.Local: 
        from dotenv import load_dotenv
        _ = load_dotenv()
    taken_google_config = environ.get("GOOGLE_CONFIG")
    assert taken_google_config != None, "No data provided for google config"
    google_config = GoogleConfig.model_validate_json(taken_google_config)
    taken_db_config = environ.get("DB_CONFIG")
    assert taken_db_config != None, "No data provided for db onfig"
    db_config = DbConfig.model_validate_json(taken_db_config)

    return AppConfig(
        google_config =google_config, 
        db_config = db_config,
        environment = environment
    )

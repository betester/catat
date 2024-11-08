
from sqlalchemy.engine import Engine
from sqlmodel.main import SQLModel
from conf import DbConfig, Environment
from sqlmodel import create_engine

def init_db(db_conf: DbConfig, environment: Environment) -> Engine:

    engine = create_engine(url=db_conf.db_url, connect_args=db_conf.connect_args)
    if environment == Environment.Local: SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    return engine

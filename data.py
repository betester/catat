from enum import StrEnum
from datetime import datetime
from sqlmodel import SQLModel, Field

class CatatUser(SQLModel, table=True):
    email: str = Field(primary_key=True)  # primary_key implies uniqueness
    full_name: str = Field(nullable=False, unique=True)
    profile_picture: str = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class DataType(StrEnum):
    HTML = "text/html"
    PDF = "application/pdf"
    UNSUPPORTED  = ""

    @classmethod
    def parse(cls, content_type: str) -> 'DataType':
        values = list(cls)

        for value in values:
            if value.value in content_type:
                return value
    
        return DataType.UNSUPPORTED

    def get_file_extension(self) -> str:
        if self == DataType.PDF:
            return ".pdf"
        elif self == DataType.HTML:
            return ".html"
        else:
            return ""

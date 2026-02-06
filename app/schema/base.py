from datetime import datetime
from pydantic import BaseModel

class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
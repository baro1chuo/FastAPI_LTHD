from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

class ReviewOut(BaseModel):
    id: int
    animal_id: int
    user_id: int
    rating: int
    content: str
    status: ReviewStatus
    created_at: datetime

    model_config = {"from_attributes": True}

class ReviewCreate(BaseModel):
    animal_id: int
    user_id: int
    rating: int = Field(ge=1, le=5)
    content: str = Field(max_length=500)
    lang: str

class ReviewStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    hidden = "hidden"

class ReviewStatusUpdate(BaseModel):
    status: ReviewStatus
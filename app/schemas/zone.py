from pydantic import BaseModel

class ZoneOut(BaseModel):  #tra ve theo ngon ngu
    id: int
    name: str
    description: str | None = None
    image_url: str | None = None
    model_config = {"from_attributes": True}

class ZoneCreate(BaseModel):
    name: str
    description: str | None = None
    image_url: str | None = None
    lang: str

class ZoneUpdate(BaseModel):
    name: str
    description: str | None = None
    image_url: str | None = None

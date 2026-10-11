from pydantic import BaseModel

class AnimalCreate(BaseModel):
    name: str 
    scientific_name: str | None = None
    description: str | None = None
    image_url: str | None = None
    catagory_id: int | None = None
    zone_id: int | None = None
    conservation_status_id: int | None = None



class AnimalDetail(BaseModel):
    scientific_name: str | None = None
    description: str | None = None
    conservation_status: str | None = None

class AnimalListItem(BaseModel):
    id: int
    name: str
    image_url: str | None = None
    category_id: int | None = None
    zone_id: int | None = None
    
    model_config = {"from_attributes": True}

class AnimalUpdate(BaseModel):
    name: str | None = None
    scientific_name: str | None = None
    description: str | None = None
    image_url: str | None = None
    catagory_id: int | None = None
    zone_id: int | None = None
    conservation_status_id: int | None = None
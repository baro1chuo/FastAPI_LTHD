from pydantic import BaseModel

class DashboardOut(BaseModel):
    total_animals: int
    total_zones: int
    total_users: int
    pending_reviews: int


class SettingsOut(BaseModel):
    opening_hours: str
    hotline: str
    default_language: str
    auto_approve_reviews: bool


class SettingsUpdate(BaseModel):
    opening_hours: str | None = None
    hotline: str | None = None
    default_language: str | None = None
    auto_approve_reviews: bool | None = None
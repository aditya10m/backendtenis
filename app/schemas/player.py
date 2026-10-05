from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class PlayerProfileBase(BaseModel):
    full_name: Optional[str] = None
    playing_hand: Optional[str] = None
    backhand_type: Optional[str] = None
    skill_level: Optional[str] = None
    preferred_surface: Optional[str] = None
    height_cm: Optional[int] = None
    age: Optional[int] = None
    country: Optional[str] = None
    coach_name: Optional[str] = None
    training_frequency: Optional[str] = None
    avatar_url: Optional[str] = None

class PlayerProfileCreate(PlayerProfileBase):
    pass

class PlayerProfileUpdate(PlayerProfileBase):
    pass

class PlayerProfileResponse(PlayerProfileBase):
    id: UUID
    user_id: UUID
    email: Optional[str] = None
    statistics: Optional[dict] = None

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.player import PlayerProfileCreate, PlayerProfileUpdate, PlayerProfileResponse
from app.services.player_service import PlayerService

router = APIRouter()

@router.get("/me", response_model=PlayerProfileResponse)
async def get_my_profile(current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    player_service = PlayerService(db)
    profile = await player_service.get_profile(current_user.id)
    if not profile:
        profile = await player_service.create_profile(current_user.id, PlayerProfileCreate(
            playing_hand="right",
            backhand_type="two_handed",
            skill_level="intermediate",
            preferred_surface="Hard",
            height_cm=180,
            age=25
        ))
    
    # Return with current user's name and email
    resp = PlayerProfileResponse.model_validate(profile, from_attributes=True)
    resp.full_name = current_user.full_name
    resp.email = current_user.email
    return resp

@router.put("/me", response_model=PlayerProfileResponse)
async def update_my_profile(profile_data: PlayerProfileUpdate, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    player_service = PlayerService(db)
    
    # If full_name is provided, update on the user record
    if profile_data.full_name and profile_data.full_name.strip():
        current_user.full_name = profile_data.full_name.strip()
        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)

    # Exclude full_name from player_profile table update
    profile_dict = profile_data.model_dump(exclude={"full_name"}, exclude_unset=True)
    profile_update = PlayerProfileUpdate(**profile_dict)
    
    profile = await player_service.update_profile(current_user.id, profile_update)
    resp = PlayerProfileResponse.model_validate(profile, from_attributes=True)
    resp.full_name = current_user.full_name
    resp.email = current_user.email
    return resp

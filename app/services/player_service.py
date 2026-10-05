from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.player_profile import PlayerProfile
from app.schemas.player import PlayerProfileUpdate

class PlayerService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_profile(self, user_id):
        result = await self.db.execute(select(PlayerProfile).where(PlayerProfile.user_id == user_id))
        return result.scalar_one_or_none()
        
    async def create_profile(self, user_id, data):
        profile = PlayerProfile(user_id=user_id, **data.model_dump())
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile
        
    async def update_profile(self, user_id, data: PlayerProfileUpdate):
        profile = await self.get_profile(user_id)
        if not profile:
            return await self.create_profile(user_id, data)
            
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, key, value)
            
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

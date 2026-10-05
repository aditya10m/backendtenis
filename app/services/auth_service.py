from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin
from app.core.security import get_password_hash, verify_password, create_access_token

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def register_user(self, data: UserRegister):
        result = await self.db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")
            
        new_user = User(
            email=data.email,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        
        token = create_access_token(subject=new_user.id)
        return {"access_token": token, "token_type": "bearer", "user": new_user}
        
    async def authenticate_user(self, data: UserLogin):
        result = await self.db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        token = create_access_token(subject=user.id)
        return {"access_token": token, "token_type": "bearer", "user": user}
        
    async def refresh_token(self, current_user):
        token = create_access_token(subject=current_user.id)
        return {"access_token": token, "token_type": "bearer", "user": current_user}

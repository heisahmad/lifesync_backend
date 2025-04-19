from sqlalchemy.orm import Session
from typing import Optional
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.auth import get_password_hash, verify_password

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, user_create: UserCreate) -> User:
        hashed_password = get_password_hash(user_create.password)
        db_user = User(
            email=user_create.email,
            hashed_password=hashed_password,
            is_active=True
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    def update_user(self, user: User, user_update: UserUpdate) -> User:
        if user_update.password:
            user.hashed_password = get_password_hash(user_update.password)
        if user_update.email:
            user.email = user_update.email
        self.db.commit()
        self.db.refresh(user)
        return user

# Create standalone functions that use the service for backward compatibility
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    service = UserService(db)
    return service.get_user_by_email(email)

def create_user(db: Session, user_create: UserCreate) -> User:
    service = UserService(db)
    return service.create_user(user_create)

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    service = UserService(db)
    return service.authenticate_user(email, password)

def update_user(db: Session, user: User, user_update: UserUpdate) -> User:
    service = UserService(db)
    return service.update_user(user, user_update)

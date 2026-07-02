"""Authentication service: password hashing, JWT tokens, user management."""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plain-text password."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain-text password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def decode_access_token(token: str) -> Optional[dict]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except JWTError:
            return None

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.password_hash:
            return None
        if not AuthService.verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get a user by email address."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get a user by their ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get a user by username."""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def create_user(
        db: Session,
        username: str,
        email: str,
        password: str,
        full_name: str = "",
        first_name: str = "",
        last_name: str = "",
        phone: str = None,
        company: str = None,
        role: str = "customer",
    ) -> User:
        """Create a new user account."""
        if full_name and not (first_name or last_name):
            parts = full_name.strip().split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=AuthService.hash_password(password),
            phone=phone,
            company=company,
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_oauth_user(
        db: Session,
        email: str,
        first_name: str,
        last_name: str,
        oauth_provider: str,
        oauth_id: str,
        avatar_url: str = None,
    ) -> User:
        """Create a user from OAuth (Google/Apple) login."""
        username = email.split("@")[0]
        # Ensure unique username
        base_username = username
        counter = 1
        while AuthService.get_user_by_username(db, username):
            username = f"{base_username}_{counter}"
            counter += 1

        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            oauth_provider=oauth_provider,
            oauth_id=oauth_id,
            avatar_url=avatar_url,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user_session_data(user: User) -> dict:
        """Create session data dictionary from a user object."""
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "role": user.role,
            "access_level": user.access_level,
            "avatar_url": user.avatar_url,
            "is_admin": user.is_admin,
        }

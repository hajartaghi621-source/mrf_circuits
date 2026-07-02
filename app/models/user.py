"""User model for authentication and profile management."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    role = Column(String(20), default="customer", nullable=False)  # customer | admin
    access_level = Column(Integer, default=1)  # 1-5 access levels
    phone = Column(String(30), nullable=True)
    company = Column(String(200), nullable=True)
    job_title = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    oauth_provider = Column(String(20), nullable=True)  # google | apple
    oauth_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self):
        return self.role == "admin"

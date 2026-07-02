"""Favorite and BrowsingHistory models for user activity tracking."""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="favorites")
    product = relationship("Product")

    def __repr__(self):
        return f"<Favorite user={self.user_id} product={self.product_id}>"


class BrowsingHistory(Base):
    __tablename__ = "browsing_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="browsing_history")
    product = relationship("Product")

    def __repr__(self):
        return f"<BrowsingHistory user={self.user_id} product={self.product_id} at={self.viewed_at}>"

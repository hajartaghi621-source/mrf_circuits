"""Cart model for shopping cart functionality."""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="cart_items")
    product = relationship("Product")

    def __repr__(self):
        return f"<CartItem user={self.user_id} product={self.product_id} qty={self.quantity}>"

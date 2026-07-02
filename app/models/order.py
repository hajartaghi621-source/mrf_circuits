"""Order and OrderItem models for purchase tracking."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    @staticmethod
    def generate_ref():
        import uuid
        return f"ORD-{uuid.uuid4().hex[:8].upper()}"

    id = Column(Integer, primary_key=True, index=True)
    order_ref = Column(String(20), unique=True, nullable=False, index=True, default=generate_ref)  # e.g., ORD-7742-XP
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(30), default="placed")
    # Status values: placed | packed | shipped | out_for_delivery | delivered | cancelled
    shipping_address_id = Column(Integer, ForeignKey("shipping_addresses.id"), nullable=True)
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"), nullable=True)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    stripe_session_id = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    order_date = Column(DateTime, default=datetime.utcnow)
    packed_date = Column(DateTime, nullable=True)
    shipped_date = Column(DateTime, nullable=True)
    est_delivery = Column(DateTime, nullable=True)
    delivered_date = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    shipping_address = relationship("ShippingAddress")
    payment_method = relationship("PaymentMethod")

    def __repr__(self):
        return f"<Order {self.order_ref} - {self.status}>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")

    def __repr__(self):
        return f"<OrderItem {self.product_id} x{self.quantity}>"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

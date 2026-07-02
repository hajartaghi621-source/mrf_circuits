"""Payment method model matching the Stitch payment methods dashboard."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_type = Column(String(30), nullable=False)  # visa | mastercard | amex
    last_four = Column(String(4), nullable=False)
    cardholder_name = Column(String(200), nullable=False)
    expiry_month = Column(Integer, nullable=False)
    expiry_year = Column(Integer, nullable=False)
    stripe_payment_method_id = Column(String(255), nullable=True)  # Stripe PM reference
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="payment_methods")

    def __repr__(self):
        return f"<PaymentMethod {self.card_type} ****{self.last_four}>"

    @property
    def expiry_display(self):
        return f"{self.expiry_month:02d} / {self.expiry_year % 100:02d}"

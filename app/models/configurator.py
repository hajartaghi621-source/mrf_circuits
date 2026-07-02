"""RF Product Configurator quote model for the 7-step wizard."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ConfiguratorQuote(Base):
    __tablename__ = "configurator_quotes"

    id = Column(Integer, primary_key=True, index=True)
    
    @staticmethod
    def generate_ref():
        import uuid
        return f"QT-{uuid.uuid4().hex[:8].upper()}"

    quote_ref = Column(String(20), unique=True, nullable=False, index=True, default=generate_ref)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous quotes

    # Step 1: Product Type
    product_type = Column(String(50), nullable=False)  # amplifier | filter | oscillator | mixer | coupler | etc.

    # Step 2: Technology
    technology = Column(String(50), nullable=True)  # MMIC | Hybrid Design | RFIC | Microstrip | PCB-Based RF

    # Step 3: Frequency Band
    frequency_band = Column(String(100), nullable=True)
    frequency_min = Column(Numeric(10, 3), nullable=True)
    frequency_max = Column(Numeric(10, 3), nullable=True)

    # Step 4: Technical Parameters (flexible JSON)
    parameters = Column(JSON, nullable=True)

    # Step 5: Substrate & Packaging
    substrate = Column(String(100), nullable=True)
    enclosure_type = Column(String(100), nullable=True)

    # Step 6: Price Estimation & Quantity
    estimated_cost = Column(Numeric(12, 2), nullable=True)
    quantity = Column(Integer, default=1)
    contact_email = Column(String(255), nullable=True)

    # Step 7: Final Actions
    status = Column(String(20), default="pending")  # pending | reviewed | accepted | rejected
    notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="configurator_quotes")

    def __repr__(self):
        return f"<ConfiguratorQuote {self.quote_ref} - {self.product_type}>"

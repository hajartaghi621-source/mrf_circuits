"""Product and Category models for the RF components catalog."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # Icon identifier for frontend
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Relationships
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    products = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(250), unique=True, nullable=False, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock_quantity = Column(Integer, default=0)
    stock_status = Column(String(20), default="in_stock")  # in_stock | out_of_stock | new_series | pre_order
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    unit_ref = Column(String(50), nullable=True)  # e.g., "LNA-24-Q22"

    # Technical/Engineering Specs (as columns for quick querying & catalog filtering)
    frequency_min = Column(Numeric(10, 3), nullable=True)
    frequency_max = Column(Numeric(10, 3), nullable=True)
    gain = Column(Numeric(10, 2), nullable=True)
    noise_figure = Column(Numeric(10, 2), nullable=True)
    power_output = Column(Numeric(10, 2), nullable=True)

    # Technical data stored as JSON for additional flexibility
    technical_specs = Column(JSON, nullable=True)  # {parameter: {value, measurement}}
    bulk_pricing = Column(JSON, nullable=True)  # [{quantity_range, price_per_unit}]
    engineering_remarks = Column(Text, nullable=True)
    features = Column(JSON, nullable=True)  # List of feature bullet points

    # Files & Media
    image_url = Column(String(500), nullable=True)
    image_alt = Column(String(200), nullable=True)
    gallery_urls = Column(JSON, nullable=True)  # Additional product images
    datasheet_url = Column(String(500), nullable=True)
    data_file_url = Column(String(500), nullable=True)
    pcb_layout_url = Column(String(500), nullable=True)

    # Metadata
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    views_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship("Category", back_populates="products")

    def __repr__(self):
        return f"<Product {self.sku}: {self.name}>"

    @property
    def in_stock(self):
        return self.stock_quantity > 0 and self.stock_status == "in_stock"

    @property
    def formatted_price(self):
        return f"${self.price:,.2f}"

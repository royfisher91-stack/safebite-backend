
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, unique=True, index=True, nullable=False)
    barcode = Column(String, unique=True, index=True, nullable=False)

    name = Column(String, index=True, nullable=False)
    brand = Column(String, default="")
    category = Column(String, index=True, default="general")

    description = Column(Text, default="")
    ingredients_json = Column(Text, default="[]")
    allergens_json = Column(Text, default="[]")
    markets_json = Column(Text, default='["uk"]')
    age_suitability = Column(String, default="")

    safety_score = Column(Integer, default=50)  # 0-100
    safety_result = Column(String, default="Caution")  # Safe / Caution / Avoid
    ingredient_reasoning = Column(Text, default="")
    allergen_warnings = Column(Text, default="")

    serving_size = Column(String, default="")
    calories = Column(Float, default=0)
    protein = Column(Float, default=0)
    carbs = Column(Float, default=0)
    fat = Column(Float, default=0)
    sugar = Column(Float, default=0)
    salt = Column(Float, default=0)

    image_url = Column(String, default="")

    offers = relationship(
        "Offer",
        back_populates="product",
        cascade="all, delete-orphan",
    )


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)

    retailer = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False, default=0)
    currency = Column(String, default="GBP")
    in_stock = Column(Boolean, default=True)
    stock_status = Column(String, default="In stock")
    product_url = Column(String, default="")
    size_label = Column(String, default="")
    offer_text = Column(String, default="")

    product = relationship("Product", back_populates="offers"
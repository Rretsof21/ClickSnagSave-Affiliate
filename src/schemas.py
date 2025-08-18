from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Price:
    price: Optional[float] = None
    saving_basis: Optional[float] = None

@dataclass
class Product:
    asin: str
    title: str
    image: str
    product_url: str
    affiliate_url: str = ""
    pricing: Price = field(default_factory=Price)
    discount_percent: int = 0

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class CollectionStatus(str, enum.Enum):
    PENDING = "pending"
    READY = "ready"  # Order is ready for collection
    COLLECTED = "collected"
    CANCELLED = "cancelled"

class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(255), nullable=False, index=True)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    barcode = Column(String(255), nullable=False, unique=True, index=True)
    order_number = Column(String(100), nullable=True, index=True)
    items = Column(Text, nullable=True)  # JSON string of items
    status = Column(String(50), default=CollectionStatus.PENDING.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    collected_at = Column(DateTime(timezone=True), nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "customer_phone": self.customer_phone,
            "barcode": self.barcode,
            "order_number": self.order_number,
            "items": self.items,
            "status": self.status,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None
        }
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
 
from src.database.database import Base
 
 
class Customers(Base):
    __tablename__ = "customers"
 
    customer_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
 
    customer_name = Column(String(50))
    phone_no = Column(String(20))
    email = Column(String(255))
 
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String, server_default=text("'SYSTEM'"))
 
    updated_at = Column(DateTime, server_default=func.now())
    updated_by = Column(String, server_default=text("'SYSTEM'"))
 
    is_active = Column(Boolean, default=True)
 
 
class ErrorLogs(Base):
    __tablename__ = "error_logs"
 
    error_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
 
    file_name = Column(String(255))
    function_name = Column(String(255))
    error_message = Column(String)
 
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String, server_default=text("'SYSTEM'"))
 
    updated_at = Column(DateTime, server_default=func.now())
    updated_by = Column(String, server_default=text("'SYSTEM'"))
 
    is_active = Column(Boolean, default=True)
 
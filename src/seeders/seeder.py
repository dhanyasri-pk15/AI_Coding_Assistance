import uuid
from sqlalchemy.dialects.postgresql import insert
from src.database.database import AsyncSessionLocal
from src.schema.schema import Customers
 
 
sample_customers = [
    {
        "customer_id": "c1a2b3c4-d5e6-7890-abcd-ef1234567890",
        "customer_name": "John Doe",
        "phone_no": "9999999999",
        "email": "john@example.com",
    },
    {
        "customer_id": "a1b2c3d4-e5f6-7890-abcd-ef9876543210",
        "customer_name": "Jane Smith",
        "phone_no": "8888888888",
        "email": "jane@example.com",
    },
]
 
 
async def seed_customers():
 
    async with AsyncSessionLocal() as session:
 
        for customer in sample_customers:
 
            stmt = insert(Customers).values(
                customer_id=uuid.UUID(customer["customer_id"]),
                customer_name=customer["customer_name"],
                phone_no=customer["phone_no"],
                email=customer["email"],
            )
 
            # Prevent duplicate primary key error
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["customer_id"]
            )
 
            await session.execute(stmt)
 
        await session.commit()
 
 
import strawberry
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import httpx
from app.config import settings

# --- Types ---

@strawberry.type
class OrderItemType:
    id: int
    offer_id: int
    quantity: int
    order_id: int

@strawberry.type
class OrderType:
    id: int
    user_id: str
    order_status: str
    payment_status: str
    payment_id: Optional[int]
    created_at: datetime
    items: List[OrderItemType]

@strawberry.input
class OrderItemInput:
    offer_id: int
    quantity: int

@strawberry.input
class CreateOrderInput:
    user_id: str
    items: List[OrderItemInput]
    amount: Decimal

@strawberry.type
class PaymentType:
    id: int
    order_id: int
    user_id: str
    amount: Decimal
    currency: str
    payment_method: str
    payment_status: str
    provider: str
    transaction_id: str
    created_at: datetime
    updated_at: datetime

# --- Helper Function for Data Mapping ---

def map_payment_data(p: dict) -> PaymentType:
    """Safely converts JSON dictionary to PaymentType with correct types."""
    if isinstance(p.get("created_at"), str):
        p["created_at"] = datetime.fromisoformat(p["created_at"].replace("Z", "+00:00"))
    if isinstance(p.get("updated_at"), str):
        p["updated_at"] = datetime.fromisoformat(p["updated_at"].replace("Z", "+00:00"))
    
    # Ensure amount is a Decimal object, not a string/float from JSON
    if "amount" in p:
        p["amount"] = Decimal(str(p["amount"]))
        
    return PaymentType(**p)

def map_order_data(o: dict) -> OrderType:
    """Safely converts JSON dictionary to OrderType."""
    if isinstance(o.get("created_at"), str):
        o["created_at"] = datetime.fromisoformat(o["created_at"].replace("Z", "+00:00"))
    
    if "items" in o:
        o["items"] = [OrderItemType(**item) for item in o["items"]]
        
    return OrderType(**o)

# --- Resolvers ---

@strawberry.type
class Query:
    @strawberry.field
    async def get_orders(self, info) -> List[OrderType]:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        async with httpx.AsyncClient() as client:
            try:
                # Note: Removed trailing slash if your FastAPI route doesn't strictly require it
                response = await client.get(
                    f"{settings.ORDER_SERVICE_URL}/orders", 
                    headers={"X-Tenant-ID": tenant_id},
                    timeout=settings.REQUEST_TIMEOUT,
                    follow_redirects=True
                )
                if response.status_code != 200:
                    return []

                
                return [map_order_data(o) for o in response.json()]
            except Exception as e:
                raise Exception(f"Order service error: {str(e)}")
    
    @strawberry.field
    async def get_payments(self, info) -> List[PaymentType]:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.PAYMENT_SERVICE_URL}/payments", 
                    headers={"X-Tenant-ID": tenant_id},
                    timeout=settings.REQUEST_TIMEOUT,
                    follow_redirects=True
                )
                print(response.status_code, response.text)
                if response.status_code != 200:
                    return []
                
                return [map_payment_data(p) for p in response.json()]
            except Exception as e:
                raise Exception(f"Payment service error: {str(e)}")

@strawberry.type
class Mutation:
    @strawberry.field
    async def create_order(self, info, input: CreateOrderInput) -> OrderType:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ORDER_SERVICE_URL}/orders",
                json={
                    "user_id": input.user_id,
                    "items": [{"offer_id": i.offer_id, "quantity": i.quantity} for i in input.items],
                    "amount": str(input.amount)
                },
                headers={"X-Tenant-ID": tenant_id},
                follow_redirects=True
            )
            if response.status_code not in [200, 201]:
                raise Exception(f"Order creation failed: {response.text}")
            
            return map_order_data(response.json())

    @strawberry.field
    async def confirm_payment(self, info, payment_id: int) -> PaymentType:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        async with httpx.AsyncClient() as client:
            url = f"{settings.PAYMENT_SERVICE_URL}/payments/{payment_id}/confirm"
            response = await client.post(url, headers={"X-Tenant-ID": tenant_id}, follow_redirects=True)
            
            if response.status_code != 200:
                raise Exception(f"Payment confirmation failed: {response.text}")
            
            return map_payment_data(response.json())

schema = strawberry.Schema(query=Query, mutation=Mutation)
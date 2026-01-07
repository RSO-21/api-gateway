import strawberry
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import httpx
from app.config import settings
from math import cos, radians

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

@strawberry.type
class PartnerType:
    id: str
    name: str
    address: Optional[str]
    city: Optional[str]
    active: bool
    tenant_id: Optional[str]
    latitude: float
    longitude: float

@strawberry.input
class CreatePartnerInput:
    name: str
    active: bool
    latitude: float
    longitude: float
    address: str

@strawberry.input
class PartnerUpdateInput:
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    active: Optional[bool] = None
    tenant_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

@strawberry.type
class OfferType:
    id: int
    partner_id: str
    title: str
    description: Optional[str]
    price_original: float
    price_discounted: float
    quantity_total: int
    quantity_available: int
    pickup_from: datetime
    pickup_until: datetime
    status: str = "ACTIVE"
    tenant_id: Optional[str]

@strawberry.input
class CreateOfferInput:
    partner_id: str
    title: str
    description: Optional[str]
    price_original: float
    price_discounted: float
    quantity_total: int
    quantity_available: int
    pickup_from: datetime
    pickup_until: datetime
    tenant_id: Optional[str]

@strawberry.input
class OfferUpdateInput:
    partner_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    price_original: Optional[float] = None
    price_discounted: Optional[float] = None
    quantity_total: Optional[int] = None
    quantity_available: Optional[int] = None
    pickup_from: Optional[datetime] = None
    pickup_until: Optional[datetime] = None
    tenant_id: Optional[str] = None

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

def map_partner_data(data: dict) -> PartnerType:
    return PartnerType(
        id=data["id"],
        name=data["name"],
        address=data.get("address"),
        city=data.get("city", None),
        active=data.get("active", True),
        tenant_id=data.get("tenant_id", None),
        latitude=data["latitude"],
        longitude=data["longitude"]
    )

def map_offer_data(data: dict) -> OfferType:
    if not isinstance(data.get("pickup_from"), str):
        data["pickup_from"] = datetime.fromisoformat(data["pickup_from"].replace("Z", "+00:00"))
    if not isinstance(data.get("pickup_until"), str):
        data["pickup_until"] = datetime.fromisoformat(data["pickup_until"].replace("Z", "+00:00"))
    
    return OfferType(
        id=data["id"],
        partner_id=data["partner_id"],
        title=data["title"],
        description=data.get("description"),
        price_original=data["price_original"],
        price_discounted=data["price_discounted"],
        quantity_total=data["quantity_total"],
        quantity_available=data["quantity_available"],
        pickup_from=data["pickup_from"],
        pickup_until=data["pickup_until"],
        status=data.get("status", "ACTIVE"),
        tenant_id=data.get("tenant_id")
    )

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
    

    @strawberry.field
    async def all_partners(self, info) -> List[PartnerType]:
        print("here")
        # 1. Pridobimo request iz contexta, da lahko preberemo headerje
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        print("after tenant")
        # 2. Uporabimo httpx za klic na Partner mikrostoritev
        async with httpx.AsyncClient() as client:
            print(f"{settings.PARTNER_SERVICE_URL}/partners")
            try:
                response = await client.get(
                    f"{settings.PARTNER_SERVICE_URL}/partners", # URL tvoje mikrostoritve
                    headers={"X-Tenant-ID": tenant_id},
                    timeout=settings.REQUEST_TIMEOUT,
                    follow_redirects=True
                )
                
                if response.status_code != 200:
                    return []
                
                # 3. Pretvorimo JSON odgovor v seznam PartnerType objektov
                # map_partner_data je tvoja funkcija, ki preslika JSON v GraphQL tip
                return [map_partner_data(p) for p in response.json()]
                
            except Exception as e:
                # 4. Centralizirano javljanje napak
                raise Exception(f"Partner service communication error: {str(e)}")

    @strawberry.field
    async def partner_by_id(self, info, partner_id: str) -> Optional[PartnerType]:
        # 1. Priprava requesta in tenant ID-ja
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        # 2. HTTP klic na Partner mikrostoritev
        async with httpx.AsyncClient() as client:
            try:
                # URL vsebuje ID partnerja
                url = f"{settings.PARTNER_SERVICE_URL}/partners/{partner_id}"
                
                response = await client.get(
                    url, 
                    headers={"X-Tenant-ID": tenant_id},
                    timeout=settings.REQUEST_TIMEOUT,
                    follow_redirects=True
                )

                print(response.status_code, response.text)
                
                # Če partnerja ni (404), vrnemo None
                if response.status_code == 404:
                    return None
            
                    
                if response.status_code != 200:
                    raise Exception(f"Partner service returned {response.status_code}")
                
                # 3. Mapiranje rezultata
                partner_json = response.json()
                return map_partner_data(partner_json)
                
            except Exception as e:
                raise Exception(f"Error fetching partner {partner_id}: {str(e)}")

    @strawberry.field
    async def nearby_partners(self, info, lat: float, lng: float, radius_km: float = 5.0) -> List[PartnerType]:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        # 2. HTTP klic na Partner mikrostoritev
        async with httpx.AsyncClient() as client:
            try:
                # URL vsebuje ID partnerja
                url = f"{settings.PARTNER_SERVICE_URL}/partners/nearby"

                params = {
                    "lat": lat,
                    "lng": lng,
                    "radius_km": radius_km
                }
                
                response = await client.get(
                    url, 
                    headers={"X-Tenant-ID": tenant_id},
                    timeout=settings.REQUEST_TIMEOUT,
                    follow_redirects=True,
                    params=params
                )
                
                # Če partnerja ni (404), vrnemo None
                if response.status_code == 404:
                    return None
            
                    
                if response.status_code != 200:
                    raise Exception(f"Partner service returned {response.status_code}")
                
                # 3. Mapiranje rezultata
                partner_json = response.json()
                return [map_partner_data(p) for p in partner_json]
                
            except Exception as e:
                raise Exception(f"Error fetching nearby partners at ({lat, lng}): {str(e)}")
    
    @strawberry.field
    async def get_offers(self, info) -> List[OfferType]:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.OFFER_SERVICE_URL}/offers", 
                    headers={"X-Tenant-ID": tenant_id},
                    timeout=settings.REQUEST_TIMEOUT,
                    follow_redirects=True
                )
                print(response.status_code, response.text)
                if response.status_code != 200:
                    return []
                
                return [map_offer_data(p) for p in response.json()]
            except Exception as e:
                raise Exception(f"Payment service error: {str(e)}")

    @strawberry.field
    async def offer_by_id(self, info, offer_id: int) -> Optional[OfferType]:
        # 1. Priprava requesta in tenant ID-ja
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        # 2. HTTP klic na Partner mikrostoritev
        async with httpx.AsyncClient() as client:
            try:
                # URL vsebuje ID partnerja
                url = f"{settings.OFFER_SERVICE_URL}/offers/{offer_id}"
                
                response = await client.get(
                    url, 
                    headers={"X-Tenant-ID": tenant_id},
                    timeout=settings.REQUEST_TIMEOUT,
                    follow_redirects=True
                )
                
                # Če partnerja ni (404), vrnemo None
                if response.status_code == 404:
                    return None
            
                    
                if response.status_code != 200:
                    raise Exception(f"Offer service returned {response.status_code}")
                
                # 3. Mapiranje rezultata
                offer_json = response.json()
                return map_offer_data(offer_json)
                
            except Exception as e:
                raise Exception(f"Error fetching offer {offer_id}: {str(e)}")

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
    async def create_partner(self, info, input: CreatePartnerInput) -> PartnerType:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        async with httpx.AsyncClient() as client:
            payload = {
                "name": input.name,
                "active": input.active,
                "address": input.address,
                "latitude": input.latitude,
                "longitude": input.longitude
            }
            
            response = await client.post(
                f"{settings.PARTNER_SERVICE_URL}/partners",
                json=payload,
                headers={"X-Tenant-ID": tenant_id},
                follow_redirects=True
            )
            if response.status_code not in [200, 201]:
                raise Exception(f"Partner creation failed: {response.text}")
            
            return map_partner_data(response.json())

    @strawberry.mutation
    async def update_partner(self, info, partner_id: str, input: PartnerUpdateInput) -> PartnerType:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        update_data = strawberry.asdict(input)
        update_data = {k: v for k, v in update_data.items() if v is not None}

        async with httpx.AsyncClient() as client:
            url = f"{settings.PARTNER_SERVICE_URL}/partners/{partner_id}"
            
            # 3. Make the remote call
            response = await client.put(
                url, 
                json=update_data, 
                headers={"X-Tenant-ID": tenant_id}
            )
            
            # 4. Handle Errors
            if response.status_code == 404:
                raise Exception(f"Partner {partner_id} not found in remote service.")
            elif response.status_code != 200:
                raise Exception(f"Failed to update partner: {response.text}")

            # 5. Return the updated object
            return PartnerType(**response.json())

    @strawberry.mutation
    async def delete_partner(self, info, partner_id: str) -> bool:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        async with httpx.AsyncClient() as client:
            url = f"{settings.PARTNER_SERVICE_URL}/partners/{partner_id}"
            response = await client.delete(url, headers={"X-Tenant-ID": tenant_id}, follow_redirects=True)
            
            if response.status_code != 204:
                raise Exception(f"Partner not successfully deleted: {response.text}")
            
            return True

    @strawberry.field
    async def create_offer(self, info, input: CreateOfferInput) -> OfferType:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        async with httpx.AsyncClient() as client:
            payload = {
                "partner_id": input.partner_id,
                "title": input.title,
                "price_original": input.price_original,
                "price_discounted": input.price_discounted,
                "quantity_total": input.quantity_total,
                "quantity_available": input.quantity_available,
                "pickup_from": input.pickup_from.isoformat(),
                "pickup_until": input.pickup_until.isoformat()
            }

            if input.description is not None:
                payload["description"] = input.description
            if input.tenant_id is not None:
                payload["tenant_id"] = input.tenant_id
            
            response = await client.post(
                f"{settings.OFFER_SERVICE_URL}/offers",
                json=payload,
                headers={"X-Tenant-ID": tenant_id},
                follow_redirects=True
            )
            if response.status_code not in [200, 201]:
                raise Exception(f"Offer creation failed: {response.text}")
            
            return map_offer_data(response.json())
    
    @strawberry.mutation
    async def update_offer(self, info, offer_id: int, input: OfferUpdateInput) -> OfferType:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        update_data = strawberry.asdict(input)
        update_data = {k: v for k, v in update_data.items() if v is not None}

        async with httpx.AsyncClient() as client:
            url = f"{settings.OFFER_SERVICE_URL}/offers/{offer_id}"
            
            # 3. Make the remote call
            response = await client.put(
                url, 
                json=update_data, 
                headers={"X-Tenant-ID": tenant_id}
            )
            
            # 4. Handle Errors
            if response.status_code == 404:
                raise Exception(f"Offer {offer_id} not found in remote service.")
            elif response.status_code != 200:
                raise Exception(f"Failed to update offer: {response.text}")

            # 5. Return the updated object
            return OfferType(**response.json())

    @strawberry.mutation
    async def delete_offer(self, info, offer_id: int) -> bool:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        async with httpx.AsyncClient() as client:
            url = f"{settings.OFFER_SERVICE_URL}/offers/{offer_id}"
            response = await client.delete(url, headers={"X-Tenant-ID": tenant_id}, follow_redirects=True)
            
            if response.status_code != 204:
                raise Exception(f"Offer not successfully deleted: {response.text}")
            
            return True

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
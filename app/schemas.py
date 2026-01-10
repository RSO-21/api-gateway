import strawberry
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import httpx
from app.config import settings
from math import cos, radians
from strawberry.scalars import JSON

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
    updated_at: datetime
    items: List[OrderItemType]
    partner_id: Optional[str] = None
    payment_id: Optional[int] = None

@strawberry.input
class OrderItemInput:
    offer_id: int
    quantity: int

@strawberry.input
class CreateOrderInput:
    user_id: str
    items: List[OrderItemInput]
    amount: Decimal
    partner_id: str

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
    expiry_date: datetime
    status: str = "ACTIVE"
    tenant_id: Optional[str]

@strawberry.input
class CreateOfferInput:
    partner_id: str
    title: str
    description: Optional[str]
    price_original: float
    price_discounted: float
    expiry_date: datetime
    tenant_id: Optional[str]

@strawberry.input
class OfferUpdateInput:
    partner_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    price_original: Optional[float] = None
    price_discounted: Optional[float] = None
    expiry_date: datetime
    tenant_id: Optional[str] = None

@strawberry.type
class NotificationType:
    id: int
    user_id: str
    type: str = "INFO"
    title: str
    message: str
    meta: Optional[JSON] = None
    is_read: bool = False

@strawberry.type
class UserType:
    id: str
    username: str
    email: str
    name: Optional[str]
    surname: Optional[str]
    address: Optional[str]
    longitude: Optional[float]
    latitude: Optional[float]
    created_at: datetime
    updated_at: datetime
    partner_id: Optional[str]

@strawberry.input
class UserUpdateInput:
    email: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    address: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    partner_id: Optional[str] = None


@strawberry.type
class LoginSuccessResponse:
    status: str = "ok"
    username: Optional[str] = None

@strawberry.input
class LoginRequest:
    username: str
    password: str

@strawberry.type
class TokenResponse:
    access_token: str
    refresh_token: Optional[str]
    id_token: Optional[str]
    token_type: str
    expires_in: int
    scope: Optional[str]

@strawberry.input
class SignupInput:
    username: str
    email: str
    password: str

@strawberry.type
class SignupResponse:
    status: str
    message: Optional[str] = None

@strawberry.type
class LogoutResponse:
    status: str

@strawberry.type
class UserMe:
    sub: str
    email: Optional[str] = None
    preferred_username: Optional[str] = None
    roles: List[str] = strawberry.field(default_factory=list)

@strawberry.type
class CheckResponse:
    message: str

@strawberry.type
class ReviewType:
    id: str
    order_id: int
    user_id: str
    partner_id: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

@strawberry.type
class ReviewCreateType:
    order_id: int
    user_id: str
    rating: int
    comment: Optional[str] = None

@strawberry.type
class ReviewOutType:
    id: str
    order_id: int
    user_id: str
    partner_id: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

@strawberry.type
class PartnerRatingOutType:
    partner_id: str
    avg_rating: float
    count: int

@strawberry.input
class RatingInput:
    order_id: int
    user_id: str
    rating: int
    comment: Optional[str] = None

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

def map_notification_data(data: dict) -> NotificationType:
    return NotificationType(
        id=data["id"],
        user_id=data["user_id"],
        type=data.get("type", "INFO"),
        title=data["title"],
        message=data["message"],
        meta=data.get("meta"),
        is_read=data.get("is_read", False)
    )

def map_review_data(data: dict) -> ReviewType:
    if isinstance(data.get("created_at"), str):
        data["created_at"] = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    if isinstance(data.get("updated_at"), str):
        data["updated_at"] = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
    
    return ReviewOutType(
        id=data["id"],
        order_id=data["order_id"],
        user_id=data["user_id"],
        partner_id=data["partner_id"],
        rating=data["rating"],
        comment=data.get("comment"),
        created_at=data["created_at"],
        updated_at=data["updated_at"]
    )

def map_user_data(data: dict) -> UserType:
    if isinstance(data.get("created_at"), str):
        data["created_at"] = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    if isinstance(data.get("updated_at"), str):
        data["updated_at"] = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
    
    return UserType(
        id=data["id"],
        username=data["username"],
        email=data["email"],
        name=data.get("name"),
        surname=data.get("surname"),
        address=data.get("address"),
        longitude=data.get("longitude"),
        latitude=data.get("latitude"),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        partner_id=data.get("partner_id")
    )

def map_offer_data(data: dict) -> OfferType:
    if not isinstance(data.get("expiry_date"), str):
        data["expiry_date"] = datetime.fromisoformat(data["expiry_date"].replace("Z", "+00:00"))
    
    return OfferType(
        id=data["id"],
        partner_id=data["partner_id"],
        title=data["title"],
        description=data.get("description"),
        price_original=data["price_original"],
        price_discounted=data["price_discounted"],
        expiry_date=data["expiry_date"],
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
                if response.status_code != 200:
                    return []
                
                return [map_payment_data(p) for p in response.json()]
            except Exception as e:
                raise Exception(f"Payment service error: {str(e)}")
    

    @strawberry.field
    async def all_partners(self, info) -> List[PartnerType]:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        # 2. Uporabimo httpx za klic na Partner mikrostoritev
        async with httpx.AsyncClient() as client:
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
    
    @strawberry.field
    async def all_notifications(self, info, user_id: str, unread_only: bool = False) -> List[NotificationType]:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.NOTIFICATION_SERVICE_URL}/notifications", # URL tvoje mikrostoritve
                    headers={"X-Tenant-ID": tenant_id},
                    timeout=settings.REQUEST_TIMEOUT,
                    follow_redirects=True,
                    params={
                        "user_id": user_id, 
                        "unread_only": unread_only
                    }
                )
                
                if response.status_code != 200:
                    return []
                
                # 3. Pretvorimo JSON odgovor v seznam PartnerType objektov
                # map_partner_data je tvoja funkcija, ki preslika JSON v GraphQL tip
                return [map_notification_data(p) for p in response.json()]
                
            except Exception as e:
                # 4. Centralizirano javljanje napak
                raise Exception(f"Partner service communication error: {str(e)}")

    @strawberry.field
    async def all_users(self, info) -> List[UserType]:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.USER_SERVICE_URL}/users", # URL tvoje mikrostoritve
                    headers={"X-Tenant-ID": tenant_id},
                    timeout=settings.REQUEST_TIMEOUT,
                    follow_redirects=True
                )
                
                if response.status_code != 200:
                    return []
                
                # 3. Pretvorimo JSON odgovor v seznam PartnerType objektov
                # map_partner_data je tvoja funkcija, ki preslika JSON v GraphQL tip
                return [map_user_data(p) for p in response.json()]
                
            except Exception as e:
                # 4. Centralizirano javljanje napak
                raise Exception(f"Partner service communication error: {str(e)}")

    @strawberry.field
    async def user_by_id(self, info, user_id: str) -> Optional[UserType]:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        async with httpx.AsyncClient() as client:
            try:
                # URL vsebuje ID partnerja
                url = f"{settings.USER_SERVICE_URL}/users/{user_id}"
                
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
                    raise Exception(f"User service returned {response.status_code}")
                
                # 3. Mapiranje rezultata
                user_json = response.json()
                return map_user_data(user_json)
                
            except Exception as e:
                raise Exception(f"Error fetching offer {user_id}: {str(e)}")
    
    @strawberry.field
    async def list_partner_reviews(self, info, partner_id: str) -> List[ReviewOutType]:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        async with httpx.AsyncClient() as client:
            try:
                # URL vsebuje ID partnerja
                url = f"{settings.REVIEW_SERVICE_URL}/reviews/partners/{partner_id}/reviews"
                
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
                    return []
                
                # 3. Mapiranje rezultata
                review_json = response.json()

                return [map_review_data(r) for r in review_json]
                
            except Exception as e:
                raise Exception(f"Error fetching review {partner_id}: {str(e)}")
    
    @strawberry.field
    async def get_partner_rating(self, info, partner_id: str) -> PartnerRatingOutType:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        async with httpx.AsyncClient() as client:
            try:
                # URL vsebuje ID partnerja
                url = f"{settings.REVIEW_SERVICE_URL}/reviews/partners/{partner_id}/rating"
                
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
                    return []
                
                # 3. Mapiranje rezultata
                review_json = response.json()

                return PartnerRatingOutType(**review_json)
                
            except Exception as e:
                raise Exception(f"Error fetching review {partner_id}: {str(e)}")
            

    @strawberry.field
    async def user_order_history(self, info, user_id: str) -> List[OrderType]:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        async with httpx.AsyncClient() as client:
            try:
                url = f"{settings.USER_SERVICE_URL}/users/{user_id}/orders"
                
                response = await client.get(
                    url, 
                    headers={"X-Tenant-ID": tenant_id},
                    timeout=settings.REQUEST_TIMEOUT,
                    follow_redirects=True
                )
                
                if response.status_code == 404:
                    return []
                    
                if response.status_code != 200:
                    raise Exception(f"User service returned {response.status_code}")
                
                orders_data = response.json()['orders']

                return [map_order_data(o) for o in orders_data]
                
            except Exception as e:
                raise Exception(f"Error fetching orders for user {user_id}: {str(e)}")
    
    @strawberry.field
    async def me(self, info: strawberry.Info) -> Optional[UserMe]:
        request = info.context["request"]
        http_client = info.context["http_client"]

        # 1. Grab cookies from the incoming browser request
        cookies = request.cookies

        # 2. Forward them to the Auth MS /me endpoint
        auth_resp = await http_client.get(
            f"{settings.AUTH_SERVICE_URL}/auth/me",
            cookies=cookies
        )

        if auth_resp.status_code != 200:
            return None

        data = auth_resp.json()
        return UserMe(**data)

    # @strawberry.field
    # async def check_auth(self, info: strawberry.Info) -> CheckResponse:
    #     request = info.context["request"]
    #     http_client = info.context["http_client"]

    #     # 1. Grab the Authorization header
    #     auth_header = request.headers.get("Authorization")
        
    #     # If this is None, the client (browser/Postman) didn't send the header
    #     if not auth_header:
    #         print("DEBUG: No Authorization header found in the incoming request")
    #         raise Exception("No Authorization header provided by client")

    #     headers = {"Authorization": auth_header}

    #     # 2. Forward to the /check endpoint
    #     auth_resp = await http_client.get(
    #         f"{settings.AUTH_SERVICE_URL}/auth/check",
    #         headers=headers
    #     )

    #     # 3. Handle the response
    #     if auth_resp.status_code != 200:
    #         # Instead of a generic "Unauthorized", we show what the Auth MS actually said
    #         ms_error = auth_resp.json().get("error", "Unauthorized")
    #         print(f"DEBUG: Auth MS rejected the request with: {ms_error}")
    #         raise Exception(f"Auth Service Error: {ms_error}")

    #     return CheckResponse(message=auth_resp.json()["message"])

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
                    "amount": str(input.amount),
                    "partner_id": input.partner_id
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
                "expiry_date": input.expiry_date.isoformat()
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
    
    @strawberry.field
    async def mark_read(self, info, notification_id: int) -> NotificationType:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        async with httpx.AsyncClient() as client:
            url = f"{settings.NOTIFICATION_SERVICE_URL}/notifications/{notification_id}/read"
            response = await client.post(url, headers={"X-Tenant-ID": tenant_id}, follow_redirects=True)
            
            if response.status_code != 200:
                raise Exception(f"Payment confirmation failed: {response.text}")
            
            return map_notification_data(response.json())
    
    @strawberry.mutation
    async def update_user(self, info, user_id: str, input: UserUpdateInput) -> UserType:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        update_data = strawberry.asdict(input)
        update_data = {k: v for k, v in update_data.items() if v is not None}

        async with httpx.AsyncClient() as client:
            url = f"{settings.USER_SERVICE_URL}/users/{user_id}"
            
            # 3. Make the remote call
            response = await client.patch(
                url, 
                json=update_data, 
                headers={"X-Tenant-ID": tenant_id}
            )
            
            # 4. Handle Errors
            if response.status_code == 404:
                raise Exception(f"User {user_id} not found in remote service.")
            elif response.status_code != 200:
                raise Exception(f"Failed to update user: {response.text}")

            # 5. Return the updated object
            return map_user_data(response.json())
    
    @strawberry.mutation
    async def login(self, info, input: LoginRequest) -> LoginSuccessResponse:
        response = info.context["response"]
        http_client = info.context["http_client"] # From your context earlier

        # 1. Forward the credentials to the Auth MS
        # No Keycloak logic here!
        auth_response = await http_client.post(
            f"{settings.AUTH_SERVICE_URL}/auth/login",
            json={"username": input.username, "password": input.password}
        )


        if auth_response.status_code != 200:
            raise Exception("Authentication failed")

        auth_cookies = auth_response.headers.get_list("set-cookie")
        for cookie_string in auth_cookies:
            response.headers.append("set-cookie", cookie_string)

        return LoginSuccessResponse(status="ok")
    
    @strawberry.mutation
    async def signup(self, info: strawberry.Info, input: SignupInput) -> SignupResponse:
        response = info.context["response"]
        http_client = info.context["http_client"]

        # 1. Forward signup to Flask Auth Microservice
        try:
            auth_resp = await http_client.post(
                f"{settings.AUTH_SERVICE_URL}/auth/signup",
                json={
                    "username": input.username,
                    "email": input.email,
                    "password": input.password
                }
            )

            # 2. Check for errors from the Microservice
            if auth_resp.status_code != 200:
                error_data = auth_resp.json()
                raise Exception(error_data.get("error", "Signup failed"))

            # 3. RELAY COOKIES: The "Messenger" part
            # Grab all 'Set-Cookie' headers from Flask and give them to the Browser
            auth_cookies = auth_resp.headers.get_list("set-cookie")
            for cookie_string in auth_cookies:
                response.headers.append("set-cookie", cookie_string)

            return SignupResponse(status="ok")

        except Exception as e:
            # This will show up in the 'errors' array in the GraphQL response
            raise Exception(f"Signup error: {str(e)}")


    @strawberry.mutation
    async def logout(self, info: strawberry.Info) -> LogoutResponse:
        response = info.context["response"]
        http_client = info.context["http_client"]

        # 1. Call the Auth Microservice logout endpoint
        auth_resp = await http_client.post(f"{settings.AUTH_SERVICE_URL}/auth/logout")

        auth_cookies = auth_resp.headers.get_list("set-cookie")
        for cookie_string in auth_cookies:
            response.headers.append("set-cookie", cookie_string)

        return LogoutResponse(status="logged_out")
    
    @strawberry.field
    async def create_review(self, info, input: RatingInput) -> ReviewOutType:
        request = info.context["request"]
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        async with httpx.AsyncClient() as client:
            payload = {
                "order_id": input.order_id,
                "user_id": input.user_id,
                "rating": input.rating
            }

            if input.comment is not None:
                payload["comment"] = input.comment
            
            response = await client.post(
                f"{settings.REVIEW_SERVICE_URL}/reviews",
                json=payload,
                headers={"X-Tenant-ID": tenant_id},
                follow_redirects=True
            )
            if response.status_code not in [200, 201]:
                raise Exception(f"Partner creation failed: {response.text}")
            
            return ReviewOutType(**response.json())


schema = strawberry.Schema(query=Query, mutation=Mutation)
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # REST API endpoints
    ORDER_SERVICE_URL: str = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000")
    PAYMENT_SERVICE_URL: str = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000")
    PARTNER_SERVICE_URL: str = os.getenv("PARTNER_SERVICE_URL", "http://partner-service:8000")
    OFFER_SERVICE_URL: str = os.getenv("OFFER_SERVICE_URL", "http://offer-service:8000")
    
    # gRPC endpoints (if needed in future)
    PAYMENT_SERVICE_HOST: str = "payment-grpc"
    PAYMENT_SERVICE_PORT: int = 50051
    
    # Connection settings
    REQUEST_TIMEOUT: float = 10.0
    
    class Config:
        env_file = ".env"

settings = Settings()
"""FastAPI dependencies."""
from fastapi import Request, HTTPException
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
from app.config import settings
from app.core.logging import logger


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, requests_per_minute: int = 30):
        """Initialize rate limiter."""
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.lock = asyncio.Lock()
    
    async def check_rate_limit(self, client_id: str) -> bool:
        """
        Check if client is within rate limit.
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if within limit, False otherwise
        """
        async with self.lock:
            now = datetime.utcnow()
            minute_ago = now - timedelta(minutes=1)
            
            # Clean old requests
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > minute_ago
            ]
            
            # Check limit
            if len(self.requests[client_id]) >= self.requests_per_minute:
                return False
            
            # Add current request
            self.requests[client_id].append(now)
            return True


# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=settings.rate_limit_per_minute)


async def check_rate_limit(request: Request):
    """
    Dependency to check rate limiting.
    
    Args:
        request: FastAPI request
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    if not settings.enable_rate_limit:
        return
    
    client_id = request.client.host
    
    if not await rate_limiter.check_rate_limit(client_id):
        logger.warning(f"Rate limit exceeded for {client_id}")
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
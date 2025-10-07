import asyncio
import time
from app.core.logging import logger
from app.core.redis_client import redis_client
from app.config import settings

class BackgroundHealthMonitor:
    """Monitor and self-heal Redis connections."""
    
    def __init__(self):
        self.running = False
        self.task = None
    
    async def start(self):
        """Start background monitoring."""
        if settings.enable_async:
            self.running = True
            self.task = asyncio.create_task(self._monitor_loop())
            logger.info("Background health monitor started")
    
    async def stop(self):
        """Stop background monitoring."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Background health monitor stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                if not redis_client.available:
                    logger.info("Health monitor: Redis unavailable, attempting reconnection...")
                    redis_client.connect(retries=3, delay=2)
                    
                    if redis_client.available:
                        logger.info("Health monitor: Redis reconnected successfully")
                    else:
                        logger.warning("Health monitor: Redis still unavailable")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}", exc_info=True)

background_monitor = BackgroundHealthMonitor()
"""Redis client for job management."""
import redis
import json
import time
import threading
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.config import settings
from app.core.logging import logger
from app.models.job import JobStatus, JobInfo


class RedisClient:
    """Redis client wrapper for job management."""
    
    def __init__(self):
        """Initialize Redis client."""
        self._client: Optional[redis.Redis] = None
        self._available = False
        self._lock = threading.Lock()

    @property
    def available(self) -> bool:
        """Thread-safe availability check."""
        with self._lock:
            return self._available
    
    @available.setter
    def available(self, value: bool):
        """Thread-safe availability setter."""
        with self._lock:
            self._available = value

    
    def connect(self, retries: int = 3, delay: int = 2) -> redis.Redis | None:
        """Establish a Redis connection with retry logic."""
        if self._client is not None:
            return self._client

        for attempt in range(1, retries + 1):
            try:
                self._client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    password=settings.redis_password,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True
                )
                # Test connection
                self._client.ping()
                logger.info("Connected to Redis successfully")
                self.available = True
                return self._client

            except Exception as e:
                logger.warning(f"Redis connection attempt {attempt}/{retries} failed: {e}")
                if attempt < retries:
                    time.sleep(delay)
                else:
                    logger.error("All Redis connection attempts failed")

        self.available = False
        self._client = None
        return None
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client."""
        if self._client is None:
            return self.connect()
        return self._client
    
    def disconnect(self):
        """Disconnect from Redis."""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Disconnected from Redis")
    
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        try:
            return self._client is not None and self._client.ping()
        except:
            self.available = False
            return False
    
    # Job Management Methods
    
    def _job_key(self, job_id: str) -> str:
        """Generate Redis key for job."""
        return f"job:{job_id}"
    
    def _job_file_key(self, job_id: str) -> str:
        """Generate Redis key for job file path."""
        return f"job:file:{job_id}"
    
    def create_job(
        self,
        job_id: str,
        file_path: str,
        params: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a new job entry.
        
        Args:
            job_id: Unique job identifier
            file_path: Path to the file to process
            params: Job parameters
            metadata: Additional metadata
            
        Returns:
            True if created successfully
        """
        try:
            job_info = {
                "job_id": job_id,
                "status": JobStatus.PENDING,
                "created_at": datetime.utcnow().isoformat(),
                "params": params,
                "metadata": metadata or {}
            }
            
            # Store job info
            self.client.setex(
                self._job_key(job_id),
                settings.job_result_ttl,
                json.dumps(job_info)
            )
            
            # Store file path separately with longer TTL
            self.client.setex(
                self._job_file_key(job_id),
                settings.job_result_ttl + 3600,  # Extra hour for cleanup
                file_path
            )
            
            logger.info(f"Job created: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create job {job_id}: {e}")
            return False
    
    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """
        Get job information.
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobInfo if found, None otherwise
        """
        try:
            job_data = self.client.get(self._job_key(job_id))
            
            if not job_data:
                return None
            
            data = json.loads(job_data)
            return JobInfo(**data)
            
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None
    
    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        progress: Optional[int] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        detail: Optional[str] = None
    ) -> bool:
        """
        Update job information.
        
        Args:
            job_id: Job identifier
            status: New status
            progress: Progress percentage
            result: Result data
            error: Error message
            detail: Error detail
            
        Returns:
            True if updated successfully
        """
        try:
            job_data = self.client.get(self._job_key(job_id))
            
            if not job_data:
                logger.warning(f"Job not found for update: {job_id}")
                return False
            
            data = json.loads(job_data)
            
            # Update fields
            if status:
                data["status"] = status
                
                if status == JobStatus.PROCESSING and "started_at" not in data:
                    data["started_at"] = datetime.utcnow().isoformat()
                elif status == JobStatus.COMPLETED:
                    data["completed_at"] = datetime.utcnow().isoformat()
                    data["progress"] = 100
                elif status == JobStatus.FAILED:
                    data["failed_at"] = datetime.utcnow().isoformat()
            
            if progress is not None:
                data["progress"] = progress
            
            if result is not None:
                data["result"] = result
            
            if error is not None:
                data["error"] = error
            
            if detail is not None:
                data["detail"] = detail
            
            # Save updated job
            self.client.setex(
                self._job_key(job_id),
                settings.job_result_ttl,
                json.dumps(data)
            )
            
            logger.debug(f"Job updated: {job_id} - Status: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}")
            return False
    
    def get_job_file_path(self, job_id: str) -> Optional[str]:
        """
        Get file path for job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            File path if found
        """
        try:
            return self.client.get(self._job_file_key(job_id))
        except Exception as e:
            logger.error(f"Failed to get file path for job {job_id}: {e}")
            return None
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete job from Redis.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if deleted
        """
        try:
            self.client.delete(self._job_key(job_id))
            self.client.delete(self._job_file_key(job_id))
            logger.info(f"Job deleted: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            return False
    
    def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 100) -> List[JobInfo]:
        """
        List jobs (limited functionality with Redis).
        
        Args:
            status: Filter by status
            limit: Maximum number of jobs
            
        Returns:
            List of JobInfo
        """
        try:
            # Scan for job keys
            jobs = []
            cursor = 0
            
            while True:
                cursor, keys = self.client.scan(cursor, match="job:*", count=100)
                
                for key in keys:
                    if key.startswith("job:file:"):
                        continue
                    
                    try:
                        job_data = self.client.get(key)
                        if job_data:
                            data = json.loads(job_data)
                            job_info = JobInfo(**data)
                            
                            if status is None or job_info.status == status:
                                jobs.append(job_info)
                                
                                if len(jobs) >= limit:
                                    return jobs
                    except Exception as e:
                        logger.warning(f"Failed to parse job from key {key}: {e}")
                        continue
                
                if cursor == 0:
                    break
            
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            return []


# Global Redis client instance
redis_client = RedisClient()
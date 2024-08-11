import os

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,  # Define the rate limiting key (usually the IP address)
    default_limits=["20000 per day", "5000 per hour"],  # Set default rate limits
    storage_uri=os.environ.get("CACHE_URL"),
)

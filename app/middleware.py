from fastapi import Request, HTTPException
from supabase_client import supabase
from functools import wraps
import logging
from typing import Callable
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_KEY")  # Store your API key in an environment variable

async def verify_api_key(request: Request):
    api_key = request.headers.get('X-API-Key')
    if api_key != API_KEY:
        logger.warning("Invalid or missing API key")
        raise HTTPException(status_code=403, detail="Invalid API key")

async def verify_token(token: str):
    try:
        user = supabase.auth.get_user(token)
        if user and user.user:
            logger.info(f"Token verified successfully for user: {user.user.id}")
            return user.user
        else:
            logger.warning("Token verification failed: User not found in response")
            return None
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        return None

async def get_current_user(request: Request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        logger.warning("No Authorization header found")
        return None

    scheme, _, token = auth_header.partition(' ')
    if scheme.lower() != 'bearer':
        logger.warning(f"Invalid authentication scheme: {scheme}")
        return None

    user = await verify_token(token)
    return user

def auth_required(func: Callable):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user = await get_current_user(request)
        if not user:
            logger.warning("Authentication required but user not found")
            raise HTTPException(status_code=401, detail="Authentication required")
        request.state.user = user
        return await func(request, *args, **kwargs)
    return wrapper

# QuantLab_Backend/app/middleware.py

from fastapi import Request, HTTPException
from supabase_client import supabase
from functools import wraps
import logging
from typing import Callable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            return {"message": "Please authenticate"}
        request.state.user = user
        return await func(request, *args, **kwargs)
    return wrapper

def optional_auth(func: Callable):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user = await get_current_user(request)
        request.state.user = user
        return await func(request, *args, **kwargs)
    return wrapper
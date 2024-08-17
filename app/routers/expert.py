from fastapi import APIRouter, Request
from app.utils import is_paid_user
from supabase_client import supabase
from app.middleware import auth_required

router = APIRouter()

@router.get("/get-all-experts", status_code=200)
async def get_all_experts(request: Request):
    res = supabase.table("experts").select("*").execute()
    return res.data

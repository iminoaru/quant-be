from fastapi import APIRouter, HTTPException, Request
from supabase_client import supabase
from app.middleware import auth_required
from datetime import datetime, date

router = APIRouter()

@router.get("/user-subscription-status", status_code=200)
@auth_required
async def get_user_subscription(request: Request, user_id: str):
    res = supabase.table("subscription").select("end_at", "customer_id").eq("user_id", user_id).execute()
    
    #comparing the end of subscription date to current tdate to check if user is paid or not
    
    
    end_at_str = res.data[0]['end_at']
    if end_at_str is None:
        return {"status": "inactive", "end_at": None, "customer_id": None}
    
    end_at_date = datetime.strptime(end_at_str, '%Y-%m-%d')
    today_date = datetime.today()
    
    if end_at_date > today_date:
        return {"status": "active", "end_at": end_at_str, "customer_id": res.data[0]['customer_id']}
    else:
        return {"status": "inactive", "end_at": end_at_str, "customer_id": res.data[0]['customer_id']}
    
    

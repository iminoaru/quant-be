from supabase_client import supabase
from datetime import datetime


async def is_paid_user(user_id: str | None):
    if not user_id:
        return False
    
    res = supabase.table("subscription").select("end_at").eq("user_id", user_id).execute()
    if not res.data:
        return False
    end_at_str = res.data[0]['end_at']
    if end_at_str is None:
        return False
    end_at_date = datetime.strptime(end_at_str, '%Y-%m-%d')
    return end_at_date > datetime.today()

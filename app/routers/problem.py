import re
from fastapi import APIRouter, HTTPException, Request
from supabase_client import supabase
from app.middleware import auth_required
from app.utils import is_paid_user
from pydantic import UUID4

router = APIRouter()

@router.get("/", status_code=200)
async def get_all_problems(request: Request):
    res = supabase.table("problems").select("problem_id", "name", "category", "difficulty", "is_paid", "unique_name", "company", "subcategory").execute()
    return res.data


@router.get("/{problem_id}", status_code=200)
async def get_problem_by_id(request: Request, problem_id: str, user_id: str):
    
    res = supabase.table("problems").select("*").eq("problem_id", problem_id).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    problem = res.data[0]
    
    if problem['is_paid']:
        is_paid = await is_paid_user(user_id)
        if not is_paid:
            raise HTTPException(status_code=403, detail="Subscription required to access this problem")
    
    return problem


@router.get("/get-id-by-name/{unique_name}")
async def get_problem_id_by_unique_name(request: Request, unique_name: str):
    print(unique_name)
    res = supabase.table("problems").select("problem_id").eq("unique_name", unique_name).execute()
    print(res)
    return res.data


@router.get("/problem-by-name/{unique_name}")
async def get_problem_by_unique_name(
    request: Request, 
    unique_name: str, 
    user_id: str = None
):
    # Fetch the current problem
    res = supabase.table("problems").select("*").eq("unique_name", unique_name).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    problem = res.data[0]
    
    if problem['is_paid']:
        is_paid = await is_paid_user(user_id)
        if not is_paid:
            raise HTTPException(status_code=403, detail="Subscription required to access this problem")
    
    # Extract the current problem number
    match = re.match(r'(\d+)\.', problem['name'])
    if not match:
        raise HTTPException(status_code=400, detail="Invalid problem name format")
    
    current_number = int(match.group(1))
    
    # Get the next problem
    next_res = supabase.table("problems").select("unique_name").ilike("name", f"{current_number + 1}.%").limit(1).execute()
    problem['next_problem'] = next_res.data[0]['unique_name'] if next_res.data else None
    
    # Get the previous problem
    prev_res = supabase.table("problems").select("unique_name").ilike("name", f"{current_number - 1}.%").limit(1).execute()
    problem['prev_problem'] = prev_res.data[0]['unique_name'] if prev_res.data else None
    
    return problem


@router.get("/get-bookmarked/", status_code=200)
@auth_required
async def get_bookmarked_problems(user_id):
    try:
        UUID4(user_id, version=4)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    res = (supabase.table("userproblems")
           .select("problem_id, problems!inner(name, difficulty, category, created_at)")
           .eq("user_id", user_id).eq("is_bookmarked", True)
           .execute())

    return res.data

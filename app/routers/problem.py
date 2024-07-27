
from fastapi import APIRouter, HTTPException, Request
from supabase_client import supabase
from app.middleware import auth_required

router = APIRouter()

@router.get("/", status_code=200)
async def get_all_problems(request: Request):
    res = supabase.table("problems").select("problem_id", "name", "category", "difficulty", "is_paid", "unique_name", "company", "subcategory").execute()
    return res.data


@router.get("/{problem_id}", status_code=200)

async def get_problem_by_id(request: Request, problem_id: str, is_paid: bool):
    res = supabase.table("problems").select("*").eq("problem_id", problem_id).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    problemData = res.data
    problem = res.data[0] 
    
    if problem['is_paid'] and not is_paid:
        return None
    
    return problemData


@router.get("/get-id-by-name/{unique_name}")
async def get_problem_id_by_unique_name(request: Request, unique_name: str):
    print(unique_name)
    res = supabase.table("problems").select("problem_id").eq("unique_name", unique_name).execute()
    print(res)
    return res.data



@router.get("/difficulty/{difficulty}", status_code=200)
@auth_required
async def get_problems_by_difficulty(request: Request, difficulty: str):
    res = supabase.table("problems").select("*").eq("difficulty", difficulty).execute()
    return res.data

@router.get("/search/{query}", status_code=200)
@auth_required
async def search_problems(request: Request, query: str):
    query = query.strip()
    response = supabase.table("problems").select("*").ilike("name", f"%{query}%").execute()
    return response.data




@router.get("/filter/", status_code=200)
async def filter_problems(
        difficulty: str | None = None,
        category: str | None = None,
        subcategory: str | None = None,
        company: str | None = None,
        search: str = ""
):
    query = supabase.table("problems").select("*")

    if difficulty:
        query = query.eq("difficulty", difficulty)

    if category:
        query = query.eq("category", category)

    if subcategory:
        query = query.eq("subcategory", subcategory)

    if company:
        query = query.eq("company", company)

    if query:
        query = query.ilike("name", f"*{search}*")

    res = query.execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="No problems found with the given filters")

    return res.data


@router.get("/get-bookmarked/", status_code=200)
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

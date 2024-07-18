
from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel
from supabase_client import supabase

from app.middleware import auth_required

router = APIRouter()


@router.post("/solving-status", status_code=200)
@auth_required
async def update_solving_status(problem_id, user_id, status: str = 'attempted', notes: str | None = None):

    unique = supabase.table("userproblems").select("*").eq("problem_id", problem_id).eq("user_id", user_id).execute()

    if unique.data:
        res = (supabase.table("userproblems").update({"status": status, "notes": notes})
               .eq("problem_id", problem_id).eq("user_id", user_id).execute())
        return res.data

    else:
        res = supabase.table("userproblems").insert({"user_id": user_id,
                                                     "problem_id": problem_id,
                                                     "status": status,
                                                     "notes": notes}).execute()

        return res.data


class Bookmark(BaseModel):
    problem_id: str
    user_id: str
    is_bookmarked: bool


@router.post("/toggle-bookmark", status_code=200)
async def update_bookmark(data: Bookmark, request: Request):

    unique = supabase.table("userproblems").select("*").eq("problem_id", data.problem_id).eq("user_id", data.user_id).execute()

    if unique.data:
        res = (supabase.table("userproblems").update({"is_bookmarked": data.is_bookmarked})
               .eq("problem_id", data.problem_id).eq("user_id", data.user_id).execute())
        return res.data

    else:
        res = supabase.table("userproblems").insert({"user_id": data.user_id,
                                                     "problem_id": data.problem_id,
                                                     "status": "not attempted",
                                                     "is_bookmarked": data.is_bookmarked}).execute()

        return res.data



class AnswerSubmit(BaseModel):
    problem_id: str
    user_id: str
    answer: bool
    notes: str



@router.post("/submit-status", status_code=200)
@auth_required
async def check_answer(request: Request, data: AnswerSubmit = Body(...)): #= Body(...)
    
    try:
        unique = supabase.table("userproblems").select("*").eq("problem_id", data.problem_id).eq("user_id", data.user_id).execute()
        isAlreadySolved = supabase.table("userproblems").select("*").eq("problem_id", data.problem_id).eq("user_id", data.user_id).eq("status", "solved").execute()

        if unique.data:
            if isAlreadySolved.data:
                return {"message": "Already solved"}

            status = "solved" if data.answer else "attempted"
            res = (supabase.table("userproblems").update({"status": status, "notes": data.notes})
                   .eq("problem_id", data.problem_id).eq("user_id", data.user_id).execute())

            return res.data
        else:
            status = "solved" if data.answer else "attempted"
            res = supabase.table("userproblems").insert({"user_id": data.user_id,
                                                         "problem_id": data.problem_id,
                                                         "status": status,
                                                         "notes": data.notes}).execute()

            return res.data

    except Exception as e:

        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.get("/get-user-problems", status_code=200)
async def get_user_problems(user_id: str, request: Request):
    try:
        res = supabase.table("userproblems").select("*").eq("user_id", user_id).execute()
        return res.data

    except Exception as e:

        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.get("/user-stats", status_code=200)
async def get_user_stats(user_id: str, request: Request):
    try:
        def get_count(result):
            print(f"Query result: {result}")
            if hasattr(result, 'count'):
                return result.count
            elif isinstance(result.data, list):
                return len(result.data)
            else:
                print(f"Count not found in result: {result}")
                return 0

        # Query for user's solved problems with difficulty
        user_problems = supabase.table("userproblems")\
            .select("problems(difficulty)")\
            .eq("user_id", user_id)\
            .eq("status", "solved")\
            .execute()

        print(f"User problems result: {user_problems}")

        # Count problems for each difficulty
        easy_count = sum(1 for problem in user_problems.data if problem['problems']['difficulty'] == 'Easy')
        medium_count = sum(1 for problem in user_problems.data if problem['problems']['difficulty'] == 'Medium')
        hard_count = sum(1 for problem in user_problems.data if problem['problems']['difficulty'] == 'Hard')

        # Query for total problems counts
        total_easy = supabase.table("problems")\
            .select("*", count="exact")\
            .eq("difficulty", "Easy")\
            .execute()
            
        total_medium = supabase.table("problems")\
            .select("*", count="exact")\
            .eq("difficulty", "Medium")\
            .execute()
            
        total_hard = supabase.table("problems")\
            .select("*", count="exact")\
            .eq("difficulty", "Hard")\
            .execute()

        return {
            "easy_count": easy_count,
            "total_easy": get_count(total_easy),
            "medium_count": medium_count,
            "total_medium": get_count(total_medium),
            "hard_count": hard_count,
            "total_hard": get_count(total_hard)
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
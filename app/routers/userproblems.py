
from collections import defaultdict
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


@router.get("/user-stats")
@auth_required
async def get_user_stats(request: Request, user_id: str):
    try:
        # Fetch all problems with their difficulty and category
        all_problems = supabase.table("problems").select("problem_id", "difficulty", "category").execute()
        
        # Create dictionaries to store total counts
        total_difficulty = defaultdict(int)
        total_category = defaultdict(int)
        
        # Count total problems for each difficulty and category
        for problem in all_problems.data:
            total_difficulty[problem['difficulty']] += 1
            total_category[problem['category']] += 1

        # Fetch user's solved problems
        user_problems = supabase.table("userproblems")\
            .select("problem_id, problems(difficulty, category)")\
            .eq("user_id", user_id)\
            .eq("status", "solved")\
            .execute()

        # Count solved problems for each difficulty and category
        difficulty_counts = defaultdict(int)
        category_counts = defaultdict(int)

        for problem in user_problems.data:
            difficulty = problem['problems']['difficulty']
            category = problem['problems']['category']
            difficulty_counts[difficulty] += 1
            category_counts[category] += 1

        # Prepare the response data
        difficulty_stats = {
            difficulty: {
                "solved": difficulty_counts[difficulty],
                "total": total_difficulty[difficulty]
            }
            for difficulty in ["Easy", "Medium", "Hard"]
        }

        category_stats = {
            category: {
                "solved": category_counts[category],
                "total": total_category[category]
            }
            for category in ["Statistics", "Probability", "Calculus", "Maths"]
        }

        return {
            "difficulty_stats": difficulty_stats,
            "category_stats": category_stats
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

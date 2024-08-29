from fastapi import APIRouter
from .problem import router as problem_router
from .user import router as user_router
from .playlist import router as playlist_router
from .userproblems import router as userproblem_router
from .chat import router as chat_router
from .expert import router as experts_router

router = APIRouter()

router.include_router(problem_router, prefix="/problems", tags=["problems"])
router.include_router(user_router, prefix="/users", tags=["users"])
router.include_router(playlist_router, prefix="/playlists", tags=["playlists"])
router.include_router(userproblem_router, prefix="/userproblems", tags=["userproblems"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(experts_router, prefix="/experts", tags=["experts"])

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.routers import user
from app.routers import problem
from app.routers import userproblems
from app.routers import playlist
from app.routers import chat
from app.routers import expert
from supabase_client import supabase
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://quantdash.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(problem.router, prefix="/problems", tags=["problems"])
app.include_router(userproblems.router, prefix="/userproblems", tags=["userproblems"])
app.include_router(playlist.router, prefix="/playlists", tags=["playlists"])

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(chat.expert, prefix="/experts", tags=["experts"])
@app.get("/")
def read_root():
    
    return {"greetings": "welcome"}


@app.get("/api/random-problem")
async def get_random_problems():
    try:
        response = supabase.rpc('get_random_question').execute()
        if response.data and len(response.data) > 0:
            return {"unique_name": response.data[0]['unique_name']}
        else:
            raise HTTPException(status_code=404, detail="No random problem found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

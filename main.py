import datetime
from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.cors import CORSMiddleware


from app.middleware import verify_api_key
from app.routers import router  # Import the aggregated router
from supabase_client import supabase
from dotenv import load_dotenv


load_dotenv()

app = FastAPI()


# Apply secure_call to all routes by default
@app.middleware("http")
async def apply_secure_call(request: Request, call_next):
    await verify_api_key(request)
    response = await call_next(request)
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the aggregated router
app.include_router(router)

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


daily_question = None
last_update = None

async def get_daily_question():
    global daily_question, last_update
    
    # Check if we need to update the daily question
    now = datetime.datetime.now()
    if not daily_question or not last_update or now.date() > last_update.date():
        try:
            response = supabase.rpc('get_daily_prob').execute()
            if response.data and len(response.data) > 0:
                daily_question = response.data[0]
                last_update = now
            else:
                raise HTTPException(status_code=404, detail="No question found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return daily_question

@app.get("/api/question-of-the-day")
async def question_of_the_day():
    question = await get_daily_question()
    
    return question

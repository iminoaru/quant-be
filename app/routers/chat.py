
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from typing import List, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from backend.app.middleware import auth_required
from backend.app.utils import is_paid_user
from backend.supabase_client import supabase
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    problem_id: str
    message: str
    user_id: str

def get_problem_details(problem_id: str) -> dict:
    res = supabase.table("problems").select("*").eq("problem_id", problem_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Problem not found")
    return res.data[0]

async def generate_response(messages: List[dict]) -> AsyncGenerator[str, None]:
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0.7,
        streaming=True,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content

@router.post("/chat")
@auth_required
async def chat(request: Request, chat_request: ChatRequest):
    try:
        if not await is_paid_user(chat_request.user_id):
            raise HTTPException(status_code=403, detail="This feature is only available for paid users")

        problem_details = get_problem_details(chat_request.problem_id)

        
        res = supabase.table("chat_history").select("*").eq("user_id", chat_request.user_id).eq("problem_id", chat_request.problem_id).order('created_at', desc=True).limit(5).execute()
        chat_history = res.data[::-1]  # Reverse to get in chronological order

        
        messages = [SystemMessage(content=f"""
        You are an AI assistant for a quant finance question platform named QuantDash.
        Refer to yourself as QuantDash Helper.
        If anything is out of context just say it is not related to this question.
        If you need to provide equations, use the following format:
        - Inline equations should be wrapped in single dollar signs: `$equation$`.
        - Block equations should be wrapped in double dollar signs: `$$equation$$`.
        Use the following problem details to answer the user's question:

        Problem: {problem_details['name']}
        Description: {problem_details['problem_text']}
        Hint: {problem_details['hints']}
        Solution: {problem_details['solution']}
        Category: {problem_details['category']}

        Provide only necessary information, add some emojis if you feel like it, be precise and straight to the point.
        """)]

        # Add the recent chat history to the messages
        for msg in chat_history:
            if msg['role'] == 'user':
                messages.append(HumanMessage(content=msg['message']))
            elif msg['role'] == 'assistant':
                messages.append(AIMessage(content=msg['message']))

        # Add the current user message
        messages.append(HumanMessage(content=chat_request.message))

        
        async def event_generator():
            full_response = ""
            async for token in generate_response(messages):
                full_response += token
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"

            # Update the chat history in the database
            supabase.table("chat_history").insert([
                {"user_id": chat_request.user_id, "problem_id": chat_request.problem_id, "role": "user", "message": chat_request.message},
                {"user_id": chat_request.user_id, "problem_id": chat_request.problem_id, "role": "assistant", "message": full_response}
            ]).execute()

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.get("/chat-history/{problem_id}")
@auth_required
async def get_chat_history(request: Request, problem_id: str, user_id: str):
    try:
        res = supabase.table("chat_history").select("*").eq("user_id", user_id).eq("problem_id", problem_id).order('created_at').execute()
        return [{"role": item["role"], "content": item["message"]} for item in res.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching chat history: {str(e)}")

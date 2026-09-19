from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from tools import get_loan_status, get_emi_schedule
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from pydantic import BaseModel, Field
import uuid
from pathlib import Path
from typing import Optional
from typing import List

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Optional session ID for maintaining chat history

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    tools_called: list[str] = Field(default_factory=list)

class WindowChatMessageHistory(BaseChatMessageHistory,BaseModel):
    messages: List[BaseMessage] = Field(default_factory=list)
    k: int = Field(default=8, description="The number of messages to keep in the sliding window.")
    def add_messages(self, messages):
        self.messages.extend(messages)
        if len(self.messages) > self.k:
            self.messages = self.messages[-self.k:]

    def clear(self):
        self.messages = []


app = FastAPI(title="BFL Chatbot API",
               description="API for BFL Chatbot", 
               version="1.0.0")



llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,  # need to discuss this in the future
)


TOOLS = [get_loan_status, get_emi_schedule]
llm_with_tools = llm.bind_tools(TOOLS)

tool_map = {
        "get_loan_status": get_loan_status,
        "get_emi_schedule": get_emi_schedule
    }


SYSTEM_PROMPT = """You are a professional Bajaj Finance customer support agent.

You have access to:
1. TOOLS  — for live loan data (status, EMI, prepayment, refund)
             Use when customer provides a Loan ID (BFL + digits)

RULES:
- Loan ID present → use tools
- Format all amounts with Rs and commas (e.g., Rs 8,450)
- Be warm, concise, and professional
- If a loan is not found, ask customer to double-check the Loan ID
"""

WINDOW_K = 8
window_store = {}

def get_session_history(session_id):
    if session_id not in window_store:
        window_store[session_id] = WindowChatMessageHistory(k=WINDOW_K)
    return window_store[session_id]



def run_chat_turn(user_message: str, session_id: str) -> str:
    history = get_session_history(session_id)
    messages = [{'role':"system","content":SYSTEM_PROMPT}]
    messages.extend(history.messages)
    messages.append(HumanMessage(content=user_message))
    tools_used = []

    response = llm_with_tools.invoke(messages)

    while response.tool_calls:
        messages.append(response)
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tools_used.append(tool_name)

            tool_fn = tool_map.get(tool_name)
            if tool_fn:
                result = tool_fn.invoke(tool_args)
            else:
                result = {"error":"tool is not available"}

            messages.append(ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]

            ))
        response = llm_with_tools.invoke(messages)

    history.add_user_message(user_message)
    history.add_ai_message(response.content)

    return response.content, tools_used




    

@app.get("/ui")
def read_root():
    home_page = Path(__file__).with_name("home.html").read_text(encoding="utf-8")
    return HTMLResponse(content=home_page, status_code=200)

@app.post("/chat",response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    reply, tools_used = run_chat_turn(request.message, session_id)
    return ChatResponse(reply=reply, session_id=session_id, tools_called=tools_used)

# @app.post("/history")
# def history_endpoint():
#     # Here you would retrieve the chat history
#     history = [
#         {"user": "Hello", "bot": "Hi there!"},
#         {"user": "How are you?", "bot": "I'm just a bot, but thanks for asking!"}
#     ]
#     return {"history": history}


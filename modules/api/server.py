from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import re

from modules.agents.graph import run_agent
from modules.config import get_settings
from modules.models import AgentMessage, ChatRequest, ChatResponse, HealthResponse

settings = get_settings()
app = FastAPI(
    title="AutoGenie Automobile Agent",
    version="0.1.0",
    description=(
        "LLM-orchestrated automobile agent with RAG-backed car discovery and finance planning option."
    ),
)

# Add the middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """ Performs a simple health check """
    return HealthResponse(
        status="ok",
        version="0.1.0",
        docs_url=None,
    )

@app.post("/api/v1/query", response_model=ChatResponse)
def query(request: ChatRequest) -> ChatResponse:
    """ 
    Query Endpoint:
    - Takes in a Chatrequest via FastAPI.
    - If min == max budget:
        - Expands the range by ±10% (or ±1000 if v is 0)
        - Stores a budget_note and surfaces in response.
    - Calls run_agent(request) to execute LangGraph pipeline.
    - Normalizes state whether it’s a dict or Pydantic model.
    - Finds last message from "answer_agent" as the primary answer.
    - Prepends budget_note if any.
    - Extracts RAG sources by scanning [source] lines from rag_context.
    - Returns a ChatResponse with answer, cars, finance_plan, sources
    """
    budget_note = None
    if (
        request.budget_min is not None
        and request.budget_max is not None
        and request.budget_min == request.budget_max
    ):
        budget = request.budget_min
        spread = budget * 0.1 if budget and budget > 0 else 1000.0
        request.budget_min = max(0.0, budget - spread)
        request.budget_max = budget + spread
        budget_note = (
            f"Your minimum and maximum budget were the same ({budget:.0f} USD); "
            f"I expanded the range to approximately {request.budget_min:.0f}–"
            f"{request.budget_max:.0f} USD for better matching."
        )

    state = run_agent(request)

    if isinstance(state, dict):
        messages = state.get("messages", []) or []
        cars = state.get("cars", []) or []
        finance_plan = state.get("finance_plan")
        rag_context = state.get("rag_context", "") or ""
    else:
        messages = state.messages
        cars = state.cars
        finance_plan = state.finance_plan
        rag_context = state.rag_context

    last_answer = next((m for m in reversed(messages) if getattr(m, "sender", "") == "answer_agent"),None,)
    answer_text = getattr(last_answer, "content", None) or "No answer generated."
    if budget_note:
        answer_text = budget_note + "\n\n" + answer_text

    sources = []
    if rag_context:
        for line in rag_context.splitlines():
            if line.startswith("[") and "]" in line:
                src = re.findall(r"\[(.*?)\]", line)
                sources.extend(src)

    return ChatResponse(
        answer=answer_text,
        cars=cars,
        finance_plan=finance_plan,
        sources=list(dict.fromkeys(sources)),
    )

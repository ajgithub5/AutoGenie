from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, HttpUrl

class Car(BaseModel):
    """
    Parameters defining the car identity availble from database
    """
    id: str
    make: str
    model: str
    year: int
    body_type: Optional[str]
    base_price_usd: float = Field(..., ge=0)
    countries_available: list[str]
    fuel_type: str
    transmission: str

class CarSearchCriteria(BaseModel):
    """
    Parameters to be considered for filtering cars.
    """
    country: str
    budget_min: Optional[float] = Field(None, ge=0)
    budget_max: Optional[float] = Field(None, ge=0)
    body_type: Optional[str] = None

class CarResult(BaseModel):
    car: Car
    reason: str

class FinancePlanRequest(BaseModel):
    """
    Parameters to be considered for Financing options.
    """
    car_price: float = Field(..., gt=0)
    down_payment: float = Field(0, ge=0)
    annual_interest_rate: float = Field(..., gt=0)
    years: int = Field(..., gt=0)

class FinancePlanSummary(BaseModel):
    """
    Provides a sample finance option with below fields.
    """
    principal: float
    monthly_payment: float
    total_interest_paid: float
    total_paid: float
    annual_interest_rate: float
    years: int

class ChatRequest(BaseModel):
    """
    Chat request initiation woith provided fields.
    """
    query: str = Field(..., description="Natural language question from the user.")
    country: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    down_payment: Optional[float] = None
    annual_rate: Optional[float] = None
    years: Optional[int] = None

class AgentDecision(BaseModel):
    """
    LLM-driven router decision for LangGraph.
    """
    next_step: Literal["car_search", "finance", "rag", "final"]
    rationale: str

class AgentMessage(BaseModel):
    """
    Simple A2A (agent-to-agent) protocol message.
    """
    sender: str
    receiver: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

class AgentState(BaseModel):
    """
    Shared state across LangGraph nodes.
    """
    messages: list[AgentMessage] = Field(default_factory=list)
    last_decision: Optional[AgentDecision] = None
    cars: list[CarResult] = Field(default_factory=list)
    finance_plan: Optional[FinancePlanSummary] = None
    rag_context: str = ""

class ChatResponse(BaseModel):
    """
    response reccieved from agents.
    """
    answer: str
    cars: list[CarResult] = Field(default_factory=list)
    finance_plan: Optional[FinancePlanSummary] = None
    sources: list[str] = Field(default_factory=list)

class HealthResponse(BaseModel):
    """
    Health checkup of the server.
    """
    status: str
    version: str
    docs_url: Optional[HttpUrl] = None


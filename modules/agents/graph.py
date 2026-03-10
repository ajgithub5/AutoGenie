from __future__ import annotations

from typing import Literal
import json

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from modules.config import get_settings
from modules.llm import get_chat_model, invoke_with_retry
from modules.models import (
    AgentDecision,
    AgentMessage,
    AgentState,
    CarSearchCriteria,
    ChatRequest,
    FinancePlanRequest,
)
from modules.rag import build_vector_store, format_docs, get_retriever
from modules.services.car_service import search_cars
from modules.services.finance_service import compute_finance_plan

settings = get_settings()
chat_model = get_chat_model()
vectorstore = build_vector_store()
retriever = get_retriever(vectorstore)

def append_message(
    state: AgentState, sender: str, receiver: str, content: str
) -> AgentState:
    """ Message generation """
    msg = AgentMessage(sender=sender, receiver=receiver, content=content)
    state.messages.append(msg)
    return state

def router_node(state: AgentState) -> AgentState:
    """ LLM Controlled router deciding which agent to act next """

    system = SystemMessage(
        content = (
            "You are a router deciding which specialist agent should handle the user.\n"
            "Options:\n"
            "- car_search: user wants car options based on budget/country.\n"
            "- finance: user wants loan / monthly payment details.\n"
            "- rag: user asks conceptual questions about car buying.\n"
            "- final: you can directly answer with existing state.\n"
            "Respond ONLY with JSON in this format: {\"next_step\": \"car_search\", \"rationale\": \"reason here\"}\n"
            "Do not include any other text."
        )
    )
    last_user = next((m for m in reversed(state.messages) if m.sender == "user"), None)

    human = HumanMessage(content= last_user.content if last_user else "")
    response = invoke_with_retry(chat_model, [system, human])

    try: 
        data = json.loads(response.content)
        if not isinstance(data, dict) or 'next_step' not in data or 'rationale' not in data:
            raise ValueError("Invalid response format")
        decision = AgentDecision(**data)
    except Exception as e:
        print(f"Router error: {e}, response: {response.content}")
        decision = AgentDecision(
            next_step= "rag",
            rationale= "Fallback to Rag due to parse error.",
        )

    state.last_decision = decision
    return append_message(
        state,
        sender = "router",
        receiver = decision.next_step,
        content = f"Routing to {decision.next_step}: {decision.rationale}",
    )

def car_search_node(state: AgentState) -> AgentState:
    """ Graph node for car search """
    last_user = next((m for m in reversed(state.messages) if m.sender == "user"), None)
    country = settings.default_country
    budget_min = None
    budget_max = None

    if last_user and last_user.metadata:
        country = last_user.metadata.get("country", country)
        budget_min = last_user.metadata.get("budget_min", None)
        budget_max = last_user.metadata.get("budget_max", None)

    criteria = CarSearchCriteria(
        country=country, budget_min=budget_min, budget_max=budget_max
    )
    state.cars = search_cars(criteria)
    return append_message(
        state,
        sender="car_agent",
        receiver="system",
        content=f"Found {len(state.cars)} cars for criteria {criteria.dict()}",
    )

def finance_node(state: AgentState) -> AgentState:
    """ 
    Graph NOde for financing options 
     - Pulls down payment, rate, years from user metadata, using defaults if absent.
     - Gets car price either from user metadata or, failing that, from the first car in state.cars.
     - If still no price, logs an error message.
     - Otherwise, builds FinancePlanRequest, calls compute_finance_plan, stores result in state.finance_plan, and logs.
    """
    last_user = next((m for m in reversed(state.messages) if m.sender == "user"), None)

    car_price = None
    down_payment = 0.0
    annual_rate = settings.default_annual_rate
    years = settings.default_loan_years

    if last_user and last_user.metadata:
        meta = last_user.metadata
        car_price = meta.get("car_price", None)

        raw_downpayment = meta.get("down_payment")
        if raw_downpayment is not None:
            down_payment = float(raw_downpayment)

        raw_rate = meta.get("annual_rate")
        if raw_rate is not None:
            annual_rate = float(raw_rate)

        raw_years = meta.get("years")
        if raw_years is not None:
            years = int(raw_years)

    if car_price is None and state.cars:
        car_price = state.cars[0].car.base_price_usd

    if car_price is None:
        return append_message(
            state,
            sender="finance_agent",
            receiver="system",
            content="Unable to compute finance plan: missing car price.",
        )

    plan_req = FinancePlanRequest(
        car_price=car_price,
        down_payment=down_payment,
        annual_interest_rate=annual_rate,
        years=years,
    )
    state.finance_plan = compute_finance_plan(plan_req)
    return append_message(
        state,
        sender="finance_agent",
        receiver="system",
        content=f"Computed finance plan for price {car_price}",
    )

def rag_node(state: AgentState) -> AgentState:
    """ 
    Node to perform RAG. 
    Uses retriever to fetch RAG docs for the user query and stores them in state.rag_context.
    """
    last_user = next((m for m in reversed(state.messages) if m.sender == "user"), None)
    query = last_user.content if last_user else ""
    docs = retriever.invoke(query)
    state.rag_context = format_docs(docs)
    return append_message(
        state,
        sender="rag_agent",
        receiver="llm",
        content=f"Retrieved {len(docs)} context documents.",
    )

def final_respond_node(state: AgentState) -> AgentState:
    """
    Compose final answer in natural language using accumulated state.
    Steps include - 
    - Collects - Car results, Finance Plan, RAG context, User Filters
    - Composes above items(from Collects) into a single contxt string.
    - Calls LLM with a specialized system prompt to produce the final answer.
    - Appends that answer as a message from "answer_agent" to "user".
    """
    last_user = next((m for m in reversed(state.messages) if m.sender == "user"), None)
    user_query = last_user.content if last_user else ""
    user_meta = last_user.metadata if last_user and last_user.metadata else {}

    system = SystemMessage(
        content=(
            "You are an automotive consultant.\n"
            "Use the provided car list, finance plan, and background docs to "
            "answer clearly and concisely.\n"
            "If there are car results, summarize them. If there is a finance "
            "plan, explain the key numbers.\n"
            "If RAG context is provided, ground your answer in it.\n"
            "The user's country and budget information are already known from the "
            "conversation context; do NOT ask the user again for their country or "
            "budget. If information is missing, make a reasonable assumption and "
            "state it briefly instead of asking for details."
        )
    )
    context_parts = []
    if state.cars:
        context_parts.append(
            "CAR_RESULTS:\n"
            + "\n".join(
                f"- {cr.car.make} {cr.car.model} {cr.car.year} "
                f"${cr.car.base_price_usd} ({cr.reason})"
                for cr in state.cars
            )
        )
    if state.finance_plan:
        fp = state.finance_plan
        context_parts.append(
            "FINANCE_PLAN:\n"
            f"Principal: {fp.principal}, Monthly: {fp.monthly_payment}, "
            f"Total interest: {fp.total_interest_paid}, Years: {fp.years}, "
            f"Rate: {fp.annual_interest_rate}%"
        )
    if state.rag_context:
        context_parts.append("BACKGROUND_DOCS:\n" + state.rag_context)

    # Include user-specified filters so the model does not ask for them again.
    if user_meta:
        context_parts.append(
            "USER_FILTERS:\n"
            f"country={user_meta.get('country')}, "
            f"budget_min={user_meta.get('budget_min')}, "
            f"budget_max={user_meta.get('budget_max')}, "
            f"down_payment={user_meta.get('down_payment')}, "
            f"annual_rate={user_meta.get('annual_rate')}, "
            f"years={user_meta.get('years')}"
        )

    composed_context = "\n\n".join(context_parts) if context_parts else "No context."
    human = HumanMessage(content=f"User question: {user_query}\n\nContext:\n{composed_context}")
    response = invoke_with_retry(chat_model, [system, human])

    return append_message(
        state,
        sender="answer_agent",
        receiver="user",
        content=response.content,
    )

def route_from_decision(state: AgentState,) -> Literal["car_search", "finance", "rag", "final"]:
    if state.last_decision is None:
        return "rag"
    return state.last_decision.next_step

def build_agent_graph() -> StateGraph:
    """ Builds the graph flow using Nodes and Edges"""

    graph = StateGraph(AgentState)

    graph.add_node("router", router_node)
    graph.add_node("car_search", car_search_node)
    graph.add_node("finance", finance_node)
    graph.add_node("rag", rag_node)
    graph.add_node("final", final_respond_node)

    graph.set_entry_point("router")

    graph.add_conditional_edges(
        "router",
        route_from_decision,
        {
            "car_search": "car_search",
            "finance": "finance",
            "rag": "rag",
            "final": "final",
        },
    )

    graph.add_edge("car_search", "finance")
    graph.add_edge("finance", "final")
    graph.add_edge("rag", "final")
    graph.add_edge("final", END)

    return graph

def run_agent(request: ChatRequest) -> AgentState:
    """
    Runs the agent - 
    - Wraps teh incoming CHatRequest into an initial AgentState(single user message with metadata).
    - Executes teh Langgraph graph.
    - Retuens the final state with car options and financing plan.
    """
    graph = build_agent_graph().compile()
    initial = AgentState(
        messages=[
            AgentMessage(
                sender="user",
                receiver="router",
                content=request.query,
                metadata={
                    "country": request.country or settings.default_country,
                    "budget_min": request.budget_min,
                    "budget_max": request.budget_max,
                    "down_payment": request.down_payment,
                    "annual_rate": request.annual_rate or settings.default_annual_rate,
                    "years": request.years or settings.default_loan_years,
                },
            )
        ]
    )
    final_state = graph.invoke(initial)
    return final_state

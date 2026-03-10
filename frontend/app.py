import os
import subprocess
import time

import httpx
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def is_backend_running(url: str) -> bool:
    try:
        resp = httpx.get(f"{url}/docs", timeout=5.0)
        return resp.status_code == 200
    except:
        return False

def start_backend():
    """Start the backend server in the background."""
    try:
        subprocess.Popen(
            ["python", "main.py"],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Wait a bit for it to start
        time.sleep(5)
    except Exception as e:
        st.error(f"Failed to start backend: {e}")

# Check if backend is running, if not, start it
if not is_backend_running(BACKEND_URL):
    st.info("Starting backend server...")
    start_backend()
    if not is_backend_running(BACKEND_URL):
        st.error("Failed to start backend server. Please run 'python main.py' manually.")
        st.stop()

st.set_page_config(page_title="AutoGenie - Car Finder", layout="wide")
st.title("AutoGenie - New Passenger Car Finder & Finance Planner")

with st.sidebar:
    st.header("Search parameters")
    country = st.text_input("Country code", value="US")
    budget_min = st.number_input("Min budget (USD)", min_value=0.0, value=20000.0)
    budget_max = st.number_input("Max budget (USD)", min_value=0.0, value=60000.0)
    down_payment = st.number_input("Down payment (USD)", min_value=0.0, value=5000.0)
    annual_rate = st.number_input(
        "Annual interest rate (%)", min_value=0.1, value=6.5
    )
    years = st.number_input("Loan term (years)", min_value=1, value=5)

user_query = st.text_area(
    "Ask about new passenger cars or financing",
    value="Show me new passenger cars available in my country within my budget, "
    "and estimate a 5-year loan after my down payment.",
    height=120,
)

if st.button("Run AutoGenie"):
    with st.spinner("Contacting AutoGenie agent..."):
        payload = {
            "query": user_query,
            "country": country or None,
            "budget_min": budget_min or None,
            "budget_max": budget_max or None,
            "down_payment": down_payment or None,
            "annual_rate": annual_rate or None,
            "years": int(years) if years else None,
        }
        try:
            resp = httpx.post(
                f"{BACKEND_URL}/api/v1/query", json=payload, timeout=60.0
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            st.error(f"Request to backend failed: {exc}")
        else:
            data = resp.json()
            st.subheader("Agent answer")
            st.write(data.get("answer"))

            cars = data.get("cars") or []
            if cars:
                st.subheader("Recommended cars")
                for cr in cars:
                    car = cr["car"]
                    st.markdown(
                        f"**{car['make']} {car['model']} ({car['year']})** - "
                        f"${car['base_price_usd']:,} - {cr['reason']}"
                    )

            plan = data.get("finance_plan")
            if plan:
                st.subheader("Finance plan (5-year example)")
                st.write(
                    f"Principal: ${plan['principal']:,}\n\n"
                    f"Monthly payment: ${plan['monthly_payment']:,}\n\n"
                    f"Total interest: ${plan['total_interest_paid']:,}\n\n"
                    f"Total paid: ${plan['total_paid']:,}"
                )

            sources = data.get("sources") or []
            if sources:
                st.subheader("Knowledge sources")
                for s in sources:
                    st.code(s)


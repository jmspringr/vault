import os

import plotly.graph_objects as go
import requests
import streamlit as st

INCOME_COLOR = "#2a78d6"
EXPENSE_COLOR = "#eb6834"


def get_api_url() -> str:
    # Streamlit Cloud provides config via st.secrets; locally fall back to env var
    try:
        if "API_URL" in st.secrets:
            return st.secrets["API_URL"].rstrip("/")
    except FileNotFoundError:
        pass
    return os.getenv("API_URL", "http://localhost:8000").rstrip("/")


API_URL = get_api_url()

st.set_page_config(page_title="Vault", layout="wide")


def api_get(path: str):
    resp = requests.get(
        f"{API_URL}{path}",
        headers={"Authorization": f"Bearer {st.session_state.token}"},
        timeout=60,
    )
    if resp.status_code == 401:
        # Token expired or invalid; send the user back to the login form
        del st.session_state.token
        st.rerun()
    resp.raise_for_status()
    return resp.json()


def login_form():
    st.title("Vault")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
    st.caption("Demo login: demo / demo123")

    if submitted:
        try:
            resp = requests.post(
                f"{API_URL}/login",
                data={"username": username, "password": password},
                timeout=60,  # free-tier API may need time to wake up
            )
        except requests.RequestException:
            st.error("Could not reach the API.")
            return
        if resp.ok:
            st.session_state.token = resp.json()["access_token"]
            st.rerun()
        else:
            st.error("Incorrect username or password.")


def dashboard():
    header, logout = st.columns([6, 1])
    header.title("Vault")
    if logout.button("Log out"):
        del st.session_state.token
        st.rerun()

    by_month = api_get("/summary/by-month")
    by_category = api_get("/summary/by-category")

    st.subheader("Income vs. expenses by month")
    if by_month:
        months = [row["month"] for row in by_month]
        fig = go.Figure([
            go.Bar(name="Income", x=months, y=[r["income"] for r in by_month],
                   marker_color=INCOME_COLOR),
            go.Bar(name="Expenses", x=months, y=[r["expenses"] for r in by_month],
                   marker_color=EXPENSE_COLOR),
        ])
        fig.update_layout(barmode="group", yaxis_tickprefix="$", yaxis_title=None,
                          legend=dict(orientation="h", y=1.1), hovermode="x unified")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No transactions yet.")

    st.subheader("Spending by category")
    if by_category:
        rows = list(reversed(by_category))  # largest bar at the top
        fig = go.Figure(go.Bar(
            x=[r["total"] for r in rows],
            y=[r["category"] for r in rows],
            orientation="h",
            marker_color=EXPENSE_COLOR,
            hovertemplate="%{y}: $%{x:,.2f}<extra></extra>",
        ))
        fig.update_layout(xaxis_tickprefix="$", margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No spending yet.")


if "token" in st.session_state:
    dashboard()
else:
    login_form()

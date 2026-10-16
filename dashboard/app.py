import os
from datetime import datetime
from html import escape
from pathlib import Path

import plotly.graph_objects as go
import requests
import streamlit as st

# Chart colors: Apple system blue + a deeper orange (validated for contrast and
# colorblind separation on the dark card surface)
INCOME_COLOR = "#0A84FF"
EXPENSE_COLOR = "#D95926"

FONT = '-apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, "Segoe UI", sans-serif'
TEXT_SECONDARY = "rgba(235,235,245,0.62)"
TEXT_TERTIARY = "rgba(235,235,245,0.36)"
GRID = "rgba(255,255,255,0.07)"


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
st.html(f"<style>{(Path(__file__).parent / 'style.css').read_text()}</style>")


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


def money(value: float) -> str:
    sign = "−" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def base_layout(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=13, color=TEXT_SECONDARY),
        margin=dict(l=0, r=8, t=8, b=0),
        hoverlabel=dict(bgcolor="#2C2C2E", bordercolor="rgba(255,255,255,0.14)",
                        font=dict(family=FONT, size=13, color="#F5F5F7")),
        showlegend=False,
    )
    axis = dict(gridcolor=GRID, zeroline=False, showline=False,
                tickfont=dict(color=TEXT_TERTIARY, size=12))
    fig.update_xaxes(**axis)
    fig.update_yaxes(**axis)
    return fig


def show_chart(fig: go.Figure):
    st.plotly_chart(fig, config={"displayModeBar": False})


def login_form():
    _, center, _ = st.columns([1, 1.15, 1])
    with center:
        with st.container(key="card-login"):
            st.markdown(
                '<div class="vt-stack-1 vt-form-header">'
                '<div class="vt-large-title" role="heading" aria-level="1">Vault</div>'
                '<div class="vt-body">Sign in to view your finances.</div>'
                "</div>",
                unsafe_allow_html=True,
            )
            with st.form("login", border=False):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In", type="primary")
            st.markdown('<div class="vt-caption">Demo account: demo / demo123</div>',
                        unsafe_allow_html=True)

            if submitted:
                try:
                    with st.spinner("Signing in…"):
                        resp = requests.post(
                            f"{API_URL}/login",
                            data={"username": username, "password": password},
                            timeout=60,  # free-tier API may need time to wake up
                        )
                except requests.RequestException:
                    st.error("Couldn't reach the server. Try again in a moment.")
                    return
                if resp.ok:
                    st.session_state.token = resp.json()["access_token"]
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")


def stat_tiles(by_month: list[dict]):
    income = sum(r["income"] for r in by_month)
    expenses = sum(r["expenses"] for r in by_month)
    tiles = [
        ("Income", money(income), INCOME_COLOR),
        ("Spending", money(expenses), EXPENSE_COLOR),
        ("Net", money(income - expenses), None),
    ]
    html = "".join(
        '<div class="vt-tile">'
        '<div class="vt-tile-label">'
        + (f'<span class="vt-dot" style="background:{color}"></span>' if color else "")
        + f"{escape(label)}</div>"
        f'<div class="vt-tile-value">{escape(value)}</div>'
        "</div>"
        for label, value, color in tiles
    )
    st.markdown(f'<div class="vt-tiles">{html}</div>', unsafe_allow_html=True)


def card_header(title: str, subtitle: str):
    st.markdown(
        '<div class="vt-stack-1 vt-card-header">'
        f'<div class="vt-title-3" role="heading" aria-level="2">{escape(title)}</div>'
        f'<div class="vt-subheadline">{escape(subtitle)}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def month_chart(by_month: list[dict]):
    months = [datetime.strptime(r["month"], "%Y-%m") for r in by_month]
    fig = go.Figure([
        go.Bar(name="Income", x=months, y=[r["income"] for r in by_month],
               marker=dict(color=INCOME_COLOR, cornerradius=4),
               hovertemplate="Income  $%{y:,.2f}<extra></extra>"),
        go.Bar(name="Spending", x=months, y=[r["expenses"] for r in by_month],
               marker=dict(color=EXPENSE_COLOR, cornerradius=4),
               hovertemplate="Spending  $%{y:,.2f}<extra></extra>"),
    ])
    base_layout(fig)
    fig.update_layout(barmode="group", bargap=0.38, bargroupgap=0.08, height=320,
                      hovermode="x unified", showlegend=True,
                      legend=dict(orientation="h", x=0, y=1.12, font=dict(size=13),
                                  itemclick=False, itemdoubleclick=False))
    fig.update_xaxes(showgrid=False, tickformat="%b", dtick="M1",
                     hoverformat="%B %Y")
    fig.update_yaxes(tickprefix="$", tickformat=",.0f", nticks=5)
    show_chart(fig)


def category_chart(by_category: list[dict]):
    rows = list(reversed(by_category))  # largest bar at the top
    fig = go.Figure(go.Bar(
        x=[r["total"] for r in rows],
        y=[r["category"] for r in rows],
        orientation="h",
        marker=dict(color=EXPENSE_COLOR, cornerradius=4),
        text=[money(r["total"]) for r in rows],
        textposition="outside",
        textfont=dict(color=TEXT_SECONDARY, size=13),
        cliponaxis=False,
        hovertemplate="%{y}  $%{x:,.2f}<extra></extra>",
    ))
    base_layout(fig)
    fig.update_layout(bargap=0.42, height=44 * len(rows) + 24)
    # Leave room past the longest bar for its value label
    fig.update_xaxes(showgrid=False, showticklabels=False,
                     range=[0, max(r["total"] for r in rows) * 1.35])
    fig.update_yaxes(showgrid=False, ticksuffix="  ",
                     tickfont=dict(color=TEXT_SECONDARY, size=13))
    show_chart(fig)


def dashboard():
    header, actions = st.columns([5, 1], vertical_alignment="center")
    with header:
        st.markdown(
            '<div class="vt-stack-1 vt-page-header">'
            '<div class="vt-large-title" role="heading" aria-level="1">Overview</div>'
            '<div class="vt-subheadline">Last 12 months · sample data</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    with actions:
        if st.button("Sign Out"):
            del st.session_state.token
            st.rerun()

    with st.spinner("Loading…"):
        by_month = api_get("/summary/by-month")
        by_category = api_get("/summary/by-category")

    if not by_month:
        st.info("No transactions yet.")
        return

    stat_tiles(by_month)

    with st.container(key="card-month"):
        card_header("Income and Spending", "Monthly totals")
        month_chart(by_month)

    with st.container(key="card-category"):
        card_header("Spending by Category", "Largest first")
        category_chart(by_category)


if "token" in st.session_state:
    dashboard()
else:
    login_form()

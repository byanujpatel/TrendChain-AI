from __future__ import annotations

import html
import json
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from crypto_pulse.config import get_settings
from crypto_pulse.models import AnalysisResult, CollectionResult, ContentItem
from crypto_pulse.pipeline import CryptoPulsePipeline
from crypto_pulse.scoring import platform_counts

st.set_page_config(
    page_title="TrendChain AI",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .stApp {
        background:
          radial-gradient(circle at 15% 0%, rgba(36, 199, 151, .08), transparent 28rem),
          #080b12;
      }
      [data-testid="stSidebar"] { background: #0d121c; }
      .block-container {
        max-width: 1180px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
      }
      .hero {
        padding: 3.1rem 3.2rem;
        border: 1px solid rgba(118, 255, 189, .18);
        border-radius: 28px;
        background:
          radial-gradient(circle at 82% 12%, rgba(111, 255, 185, .18), transparent 30%),
          linear-gradient(135deg, #101827 0%, #0b1019 68%);
        box-shadow: 0 24px 80px rgba(0, 0, 0, .3);
        margin-bottom: 1.5rem;
      }
      .eyebrow {
        color: #71f7b2;
        font-size: .76rem;
        font-weight: 800;
        letter-spacing: .16em;
        text-transform: uppercase;
      }
      .hero h1 {
        color: #f7f9fc;
        font-size: clamp(2.5rem, 6vw, 4.6rem);
        letter-spacing: -.055em;
        line-height: .98;
        margin: .65rem 0 1rem;
        max-width: 840px;
      }
      .hero p {
        color: #acb7c7;
        font-size: 1.08rem;
        line-height: 1.7;
        max-width: 720px;
      }
      .hero-badges {
        display: flex;
        flex-wrap: wrap;
        gap: .55rem;
        margin-top: 1.35rem;
      }
      .hero-badge {
        color: #c9d3e0;
        border: 1px solid #293447;
        background: rgba(15, 22, 33, .72);
        border-radius: 999px;
        font-size: .78rem;
        padding: .38rem .72rem;
      }
      .step-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: .85rem;
        margin: 1.3rem 0 1.8rem;
      }
      .step-card {
        border: 1px solid #1d2838;
        border-radius: 16px;
        background: #0d131d;
        padding: 1rem 1.05rem;
      }
      .step-number {
        color: #71f7b2;
        font-size: .72rem;
        font-weight: 800;
        letter-spacing: .12em;
      }
      .step-title { color: #edf2f8; font-weight: 750; margin: .35rem 0 .22rem; }
      .step-copy { color: #8f9bac; font-size: .86rem; line-height: 1.5; }
      .result-kicker {
        color: #71f7b2;
        font-size: .76rem;
        font-weight: 800;
        letter-spacing: .12em;
        text-transform: uppercase;
        margin-top: .8rem;
      }
      .idea-card {
        background: linear-gradient(145deg, #111925, #0e141e);
        border: 1px solid #243144;
        border-radius: 18px;
        padding: 1.25rem 1.35rem;
        margin-bottom: .9rem;
      }
      .idea-hook { color: #f5f7fb; font-size: 1.08rem; font-weight: 750; }
      .idea-topic {
        display: inline-block;
        background: rgba(113, 247, 178, .1);
        color: #71f7b2;
        padding: .2rem .55rem;
        border-radius: 999px;
        font-size: .76rem;
        margin: .45rem 0;
      }
      .muted { color: #9ca8ba; }
      div[data-testid="stMetric"] {
        background: #101722;
        border: 1px solid #202c3e;
        padding: 1rem;
        border-radius: 14px;
      }
      div[data-testid="stForm"] { border: 0; padding: 0; }
      .stButton button, .stFormSubmitButton button {
        min-height: 3rem;
        font-weight: 750;
        border-radius: 12px;
      }
      @media (max-width: 760px) {
        .hero { padding: 2rem 1.4rem; }
        .step-grid { grid-template-columns: 1fr; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def pipeline() -> CryptoPulsePipeline:
    return CryptoPulsePipeline(get_settings())


def item_dataframe(items: list[ContentItem]) -> pd.DataFrame:
    platform_labels = {
        "hackernews": "Hacker News",
        "coingecko": "CoinGecko",
        "youtube": "YouTube",
    }
    return pd.DataFrame(
        [
            {
                "Platform": platform_labels.get(item.platform, item.platform.title()),
                "Title": item.title,
                "Author": item.author,
                "Views": item.views,
                "Likes": item.likes,
                "Comments": item.comments,
                "Signal score": item.viral_score,
                "Published": item.published_at.strftime("%Y-%m-%d"),
                "URL": item.url,
            }
            for item in items
        ]
    )


def render_pattern_list(label: str, values: list[str]) -> None:
    st.markdown(f"#### {label}")
    if not values:
        st.caption("No pattern returned.")
        return
    for value in values:
        st.markdown(f"- {value}")


def render_idea(idea: dict[str, Any], index: int) -> None:
    hook = html.escape(str(idea.get("hook", "Untitled idea")))
    topic = html.escape(str(idea.get("topic", "Crypto")))
    angle = html.escape(str(idea.get("angle", "")))
    st.markdown(
        f"""
        <div class="idea-card">
          <div class="idea-hook">{index}. {hook}</div>
          <div class="idea-topic">{topic}</div>
          <div class="muted">{angle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("View outline and source evidence"):
        for beat in idea.get("outline", []):
            st.markdown(f"- {beat}")
        links = idea.get("evidence_urls", [])
        if links:
            st.markdown("**Research sources**")
            for link in links:
                safe_link = html.escape(str(link))
                st.markdown(f"- [{safe_link}]({safe_link})")


def export_payload(query: str, collection: CollectionResult, analysis: AnalysisResult) -> str:
    payload = {
        "query": query,
        "collection": {
            "used_sample_data": collection.used_sample_data,
            "errors": collection.errors,
            "items": [item.to_dict() for item in collection.items],
        },
        "analysis": analysis.to_dict(),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


settings = get_settings()
default_periods = [7, 14, 30, 90]
default_period_index = (
    default_periods.index(settings.default_days) if settings.default_days in default_periods else 2
)

st.markdown(
    """
    <section class="hero">
      <div class="eyebrow">TrendChain AI · Live Creator Intelligence</div>
      <h1>Turn today’s crypto signals into tomorrow’s viral content.</h1>
      <p>
        Search a crypto topic. TrendChain studies live videos, discussions, market trends,
        and news—then gives you evidence-backed ideas for Reels, YouTube, and Twitter.
      </p>
      <div class="hero-badges">
        <span class="hero-badge">Live multi-source research</span>
        <span class="hero-badge">Viral pattern detection</span>
        <span class="hero-badge">11 ready-to-create ideas</span>
        <span class="hero-badge">Source-backed, not guessed</span>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

with st.container(border=True):
    with st.form("research_form"):
        st.markdown("### What should we research?")
        input_col, window_col = st.columns([2.4, 1])
        with input_col:
            query = st.text_input(
                "Crypto topic or narrative",
                value=settings.default_query,
                placeholder="Try: stablecoin regulation, Solana ecosystem, Bitcoin ETF",
                help="Specific topics produce more relevant research.",
            )
        with window_col:
            days = st.selectbox(
                "Research period",
                options=default_periods,
                index=default_period_index,
                format_func=lambda value: f"Last {value} days",
                help=(
                    "Filters YouTube, Hacker News, and news by date. "
                    "CoinGecko always reflects current 24-hour trends."
                ),
            )

        with st.expander("Advanced options"):
            research_mode = st.radio(
                "Data mode",
                options=["Live Research", "Demo Data"],
                horizontal=True,
                help="Live Research uses current APIs and feeds. Demo Data is offline.",
            )
            selected_sources = st.multiselect(
                "Live sources",
                options=["youtube", "hackernews", "coingecko", "news", "reddit"],
                default=["youtube", "hackernews", "coingecko", "news"],
                format_func=lambda source: {
                    "hackernews": "Hacker News",
                    "coingecko": "CoinGecko",
                }.get(source, source.title()),
            )
            if "reddit" in selected_sources:
                st.caption("Reddit requires official Data API approval and may be unavailable.")

        run = st.form_submit_button(
            "Generate viral content ideas →",
            type="primary",
            width="stretch",
        )

st.caption(f"Last {days} days: YouTube, Hacker News, and news · CoinGecko: current 24-hour trends")

with st.sidebar:
    st.markdown("## CryptoPulse AI")
    st.caption("Live crypto research → viral content strategy")
    st.divider()
    st.markdown("#### System status")
    st.markdown(
        "🟢 **Claude**  \n" + ("Key ready" if settings.anthropic_api_key else "Local fallback")
    )
    st.markdown(
        "🟢 **YouTube**  \n" + ("Connected" if settings.youtube_api_key else "API key missing")
    )
    st.markdown(
        "🟢 **CoinGecko**  \n"
        + ("Connected" if settings.coingecko_demo_api_key else "Public endpoint")
    )
    st.markdown("🟢 **Hacker News**  \nNo key required")
    st.markdown("🟡 **Reddit**  \nApproval pending")
    st.divider()
    st.markdown("#### Every report includes")
    st.caption("5 Instagram Reel ideas")
    st.caption("3 YouTube video ideas")
    st.caption("3 Twitter thread ideas")
    st.caption("Hooks, angles, outlines, and evidence")

if not st.session_state.get("collection"):
    st.markdown(
        """
        <div class="step-grid">
          <div class="step-card">
            <div class="step-number">01 · RESEARCH</div>
            <div class="step-title">Collect live signals</div>
            <div class="step-copy">Search videos, technical discussions, market trends, and crypto news.</div>
          </div>
          <div class="step-card">
            <div class="step-number">02 · ANALYZE</div>
            <div class="step-title">Find what drives attention</div>
            <div class="step-copy">Detect trending topics, viral hooks, emotions, and story structures.</div>
          </div>
          <div class="step-card">
            <div class="step-number">03 · CREATE</div>
            <div class="step-title">Get ready-to-use ideas</div>
            <div class="step-copy">Receive 11 platform-specific ideas with outlines and source evidence.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if run:
    if not query.strip():
        st.error("Enter a crypto topic to research.")
        st.stop()
    if research_mode == "Live Research" and not selected_sources:
        st.error("Select at least one live source under Advanced options.")
        st.stop()

    with st.status("Building your creator intelligence report…", expanded=True) as status:
        st.write("1/3 Collecting current signals")
        collection = pipeline().collect(
            query=query.strip(),
            days=days,
            sources=selected_sources,
            mode="live" if research_mode == "Live Research" else "demo",
        )
        st.write(f"2/3 Ranked {len(collection.items)} relevant items")
        if not collection.items:
            status.update(label="No live evidence found", state="error", expanded=True)
            st.error(
                "No selected source returned usable live evidence. Review the errors below "
                "or switch to Demo Data."
            )
            for error in collection.errors:
                st.warning(error)
            st.stop()
        st.write("3/3 Finding patterns and creating ideas")
        analysis = pipeline().analyze(collection.items)
        status.update(label="Your content opportunities are ready", state="complete")

    st.session_state["query"] = query.strip()
    st.session_state["collection"] = collection
    st.session_state["analysis"] = analysis
    st.session_state["days"] = days

collection = st.session_state.get("collection")
analysis = st.session_state.get("analysis")
active_query = st.session_state.get("query", query)

if not collection or not analysis:
    st.stop()

for error in collection.errors:
    st.warning(error)
for warning in analysis.warnings:
    st.info(warning)

counts = platform_counts(collection.items)
st.markdown('<div class="result-kicker">Research complete</div>', unsafe_allow_html=True)
st.markdown(f"## Viral opportunities for “{html.escape(active_query)}”")

metric_cols = st.columns(4)
metric_cols[0].metric("Items analyzed", len(collection.items))
metric_cols[1].metric("Live sources", len(counts))
metric_cols[2].metric("Strongest signal", f"{collection.items[0].viral_score:.0f}/100")
metric_cols[3].metric(
    "AI strategist",
    analysis.provider.replace("claude-", "").replace("-", " ").title(),
)

ideas_tab, overview_tab, patterns_tab, evidence_tab = st.tabs(
    ["Content ideas", "Trend overview", "Why it could go viral", "Research sources"]
)

with ideas_tab:
    st.markdown("### Choose a format and start creating")
    reel_tab, youtube_tab, thread_tab = st.tabs(
        ["5 Instagram Reels", "3 YouTube videos", "3 Twitter threads"]
    )
    with reel_tab:
        for index, idea in enumerate(analysis.ideas.get("instagram_reels", []), 1):
            render_idea(idea, index)
    with youtube_tab:
        for index, idea in enumerate(analysis.ideas.get("youtube_videos", []), 1):
            render_idea(idea, index)
    with thread_tab:
        for index, idea in enumerate(analysis.ideas.get("twitter_threads", []), 1):
            render_idea(idea, index)

with overview_tab:
    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("### The opportunity")
        st.write(analysis.patterns.get("summary", ""))
        top_items = item_dataframe(collection.items[:10])
        chart = px.bar(
            top_items.sort_values("Signal score"),
            x="Signal score",
            y="Title",
            color="Platform",
            orientation="h",
            color_discrete_map={
                "Reddit": "#ff6b35",
                "YouTube": "#ff3b55",
                "Hacker News": "#ff9f1c",
                "CoinGecko": "#8ed081",
                "News": "#71f7b2",
            },
        )
        chart.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#dbe3ef",
            height=480,
            margin=dict(l=0, r=0, t=20, b=0),
            legend_title_text="",
        )
        st.plotly_chart(chart, width="stretch")
    with right:
        render_pattern_list("Trending topics", analysis.patterns.get("trending_topics", []))
        render_pattern_list("Audience emotions", analysis.patterns.get("emotions", []))
        render_pattern_list(
            "Questions viewers care about",
            analysis.patterns.get("audience_questions", []),
        )

with patterns_tab:
    col1, col2 = st.columns(2)
    with col1:
        render_pattern_list("Hooks getting attention", analysis.patterns.get("viral_hooks", []))
    with col2:
        render_pattern_list(
            "Story structures that work",
            analysis.patterns.get("storytelling_patterns", []),
        )
    st.markdown("### Headlines shaping the narrative")
    for title in analysis.patterns.get("evidence_headlines", []):
        st.markdown(f"- {title}")

with evidence_tab:
    st.caption("Every row below came from the live research stage.")
    st.dataframe(
        item_dataframe(collection.items),
        hide_index=True,
        width="stretch",
        column_config={"URL": st.column_config.LinkColumn("Open source")},
    )
    st.download_button(
        "Download full research report",
        data=export_payload(active_query, collection, analysis),
        file_name=f"crypto-pulse-{active_query.lower().replace(' ', '-')}.json",
        mime="application/json",
    )

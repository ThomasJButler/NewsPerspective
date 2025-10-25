"""
@author Tom Butler
@date 2025-10-25
@description Analytics dashboard for NewsPerspective with comprehensive metrics and visualisations.
             Displays source reliability, clickbait statistics, and trend analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from pathlib import Path


def load_source_reliability():
    """
    Load source reliability data from clickbait detector.
    @return {dict} Source reliability statistics
    """
    reliability_file = Path("data/source_reliability.json")

    if not reliability_file.exists():
        return {}

    try:
        with open(reliability_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading source reliability data: {str(e)}")
        return {}


def create_source_reliability_chart(reliability_data):
    """
    Create visualisation for source reliability metrics.
    @param {dict} reliability_data - Source reliability statistics
    @return {plotly.graph_objects.Figure} Plotly figure
    """
    if not reliability_data:
        return None

    # Prepare data
    sources = []
    avg_scores = []
    clickbait_rates = []
    total_analysed = []

    for source, stats in reliability_data.items():
        sources.append(source)
        avg_scores.append(stats.get('average_clickbait_score', 0))
        clickbait_rate = (stats.get('clickbait_count', 0) / max(stats.get('total_analyzed', 1), 1)) * 100
        clickbait_rates.append(clickbait_rate)
        total_analysed.append(stats.get('total_analyzed', 0))

    # Create DataFrame
    df = pd.DataFrame({
        'Source': sources,
        'Avg Clickbait Score': avg_scores,
        'Clickbait Rate (%)': clickbait_rates,
        'Articles Analysed': total_analysed
    })

    # Sort by average score
    df = df.sort_values('Avg Clickbait Score')

    return df


def render_source_reliability_page(reliability_data):
    """
    Render source reliability analytics page.
    @param {dict} reliability_data - Source reliability statistics
    """
    st.header("📊 Source Reliability Analysis")

    if not reliability_data:
        st.warning("No source reliability data available yet. Process some articles first!")
        return

    # Create DataFrame
    df = create_source_reliability_chart(reliability_data)

    if df is None or df.empty:
        st.warning("Insufficient data for visualisation")
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Sources Tracked", len(df))

    with col2:
        total_articles = df['Articles Analysed'].sum()
        st.metric("Total Articles", f"{total_articles:,}")

    with col3:
        avg_clickbait_score = df['Avg Clickbait Score'].mean()
        st.metric("Avg Clickbait Score", f"{avg_clickbait_score:.1f}/100")

    with col4:
        overall_clickbait_rate = df['Clickbait Rate (%)'].mean()
        st.metric("Avg Clickbait Rate", f"{overall_clickbait_rate:.1f}%")

    st.markdown("---")

    # Visualisation tabs
    tab1, tab2, tab3 = st.tabs(["📊 Reliability Scores", "🎯 Clickbait Rates", "📈 Article Volume"])

    with tab1:
        st.subheader("Average Clickbait Scores by Source")
        st.caption("Lower scores indicate more reliable, less sensational headlines")

        fig = px.bar(
            df,
            x='Avg Clickbait Score',
            y='Source',
            orientation='h',
            color='Avg Clickbait Score',
            color_continuous_scale='RdYlGn_r',
            range_color=[0, 100]
        )

        fig.update_layout(
            xaxis_title="Average Clickbait Score",
            yaxis_title="News Source",
            height=max(400, len(df) * 40),
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Clickbait Detection Rates")
        st.caption("Percentage of articles flagged as clickbait per source")

        fig = px.bar(
            df,
            x='Clickbait Rate (%)',
            y='Source',
            orientation='h',
            color='Clickbait Rate (%)',
            color_continuous_scale='Reds',
            range_color=[0, 100]
        )

        fig.update_layout(
            xaxis_title="Clickbait Rate (%)",
            yaxis_title="News Source",
            height=max(400, len(df) * 40),
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Articles Analysed per Source")
        st.caption("Total volume of articles processed from each source")

        fig = px.bar(
            df,
            x='Articles Analysed',
            y='Source',
            orientation='h',
            color='Articles Analysed',
            color_continuous_scale='Blues'
        )

        fig.update_layout(
            xaxis_title="Number of Articles",
            yaxis_title="News Source",
            height=max(400, len(df) * 40),
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    # Detailed table
    st.markdown("---")
    st.subheader("📋 Detailed Source Statistics")

    # Add reliability rating
    def get_reliability_rating(score):
        if score < 30:
            return "🟢 Highly Reliable"
        elif score < 50:
            return "🟡 Moderately Reliable"
        elif score < 70:
            return "🟠 Questionable"
        else:
            return "🔴 Unreliable"

    df['Reliability Rating'] = df['Avg Clickbait Score'].apply(get_reliability_rating)

    # Display table
    st.dataframe(
        df[['Source', 'Avg Clickbait Score', 'Clickbait Rate (%)', 'Articles Analysed', 'Reliability Rating']],
        use_container_width=True,
        hide_index=True
    )


def render_clickbait_patterns_page():
    """Render clickbait pattern analysis page."""
    st.header("🎯 Clickbait Pattern Analysis")

    st.info("This page analyses common clickbait patterns detected in headlines")

    # Simulated data for demonstration
    pattern_data = {
        'Pattern Category': [
            'Exaggeration',
            'Curiosity Gap',
            'Urgency',
            'Emotional Manipulation',
            'Listicles',
            'Sensationalism'
        ],
        'Detection Count': [245, 189, 156, 134, 98, 87],
        'Avg Score Impact': [25, 32, 18, 28, 15, 35]
    }

    df = pd.DataFrame(pattern_data)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Pattern Detection Frequency")
        fig = px.pie(
            df,
            values='Detection Count',
            names='Pattern Category',
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Average Score Impact by Pattern")
        fig = px.bar(
            df,
            x='Avg Score Impact',
            y='Pattern Category',
            orientation='h',
            color='Avg Score Impact',
            color_continuous_scale='Reds'
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Pattern examples
    st.markdown("---")
    st.subheader("Common Clickbait Phrases Detected")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🔴 Exaggeration**")
        st.markdown("- shocking\n- unbelievable\n- incredible\n- mind-blowing")

    with col2:
        st.markdown("**🟡 Curiosity Gap**")
        st.markdown("- you won't believe\n- what happened next\n- secret\n- revealed")

    with col3:
        st.markdown("**🟠 Urgency**")
        st.markdown("- breaking\n- just in\n- urgent\n- happening now")


def render_performance_metrics_page():
    """Render system performance metrics page."""
    st.header("⚡ System Performance Metrics")

    st.info("Performance statistics from recent processing runs")

    # Simulated performance data
    performance_data = {
        'Metric': [
            'Total Articles Processed',
            'Headlines Rewritten',
            'Average Processing Time',
            'Clickbait Detected',
            'API Calls Made',
            'Success Rate'
        ],
        'Value': ['2,547', '1,234', '2.3s', '487', '5,094', '98.5%'],
        'Change': ['+12%', '+8%', '-5%', '+15%', '+10%', '+0.5%']
    }

    df = pd.DataFrame(performance_data)

    # Display metrics as cards
    col1, col2, col3 = st.columns(3)

    metrics = [
        ("📊 Articles Processed", "2,547", "+12%"),
        ("✍️ Headlines Rewritten", "1,234", "+8%"),
        ("⚡ Avg Processing Time", "2.3s", "-5%"),
        ("🎯 Clickbait Detected", "487", "+15%"),
        ("📡 API Calls", "5,094", "+10%"),
        ("✅ Success Rate", "98.5%", "+0.5%")
    ]

    for i, (label, value, change) in enumerate(metrics):
        col = [col1, col2, col3][i % 3]
        with col:
            st.metric(label, value, change)

    st.markdown("---")

    # Trend chart
    st.subheader("📈 Processing Volume Trend (Last 30 Days)")

    # Simulated trend data
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    volumes = [50 + i * 2 + (i % 7) * 10 for i in range(30)]

    trend_df = pd.DataFrame({
        'Date': dates,
        'Articles Processed': volumes
    })

    fig = px.line(
        trend_df,
        x='Date',
        y='Articles Processed',
        markers=True
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Articles Processed",
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)


def main():
    """Main analytics dashboard entry point."""
    st.set_page_config(
        page_title="NewsPerspective Analytics",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
    <style>
        .main-header {
            text-align: center;
            padding: 2rem 0;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 NewsPerspective Analytics Dashboard</h1>
        <p>Comprehensive metrics and insights into news processing</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar navigation
    st.sidebar.title("📌 Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["📊 Source Reliability", "🎯 Clickbait Patterns", "⚡ Performance Metrics"]
    )

    # Load data
    reliability_data = load_source_reliability()

    # Render selected page
    if page == "📊 Source Reliability":
        render_source_reliability_page(reliability_data)
    elif page == "🎯 Clickbait Patterns":
        render_clickbait_patterns_page()
    elif page == "⚡ Performance Metrics":
        render_performance_metrics_page()


if __name__ == "__main__":
    main()

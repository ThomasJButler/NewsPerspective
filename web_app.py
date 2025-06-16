import streamlit as st
import requests
import os
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="NewsPerspective - Positive News Search",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
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
    .stat-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .news-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #28a745;
    }
    .news-card-neutral {
        border-left-color: #ffc107;
    }
    .news-card-negative {
        border-left-color: #dc3545;
    }
    .confidence-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
    }
    .confidence-high { background: #d4edda; color: #155724; }
    .confidence-medium { background: #fff3cd; color: #856404; }
    .confidence-low { background: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

# Azure Search configuration
@st.cache_data
def get_azure_config():
    return {
        'search_key': os.getenv("AZURE_SEARCH_KEY"),
        'search_endpoint': os.getenv("AZURE_SEARCH_ENDPOINT"),
        'search_index': os.getenv("AZURE_SEARCH_INDEX", "news-perspective-index")
    }

def search_articles(query="*", filter_params=None, top=20):
    """Search articles in Azure Search"""
    config = get_azure_config()
    
    if not config['search_key'] or not config['search_endpoint']:
        st.error("❌ Azure Search configuration missing. Please check your .env file.")
        return None
    
    search_url = f"{config['search_endpoint']}/indexes/{config['search_index']}/docs"
    headers = {
        "Content-Type": "application/json",
        "api-key": config['search_key']
    }
    
    # Build search parameters - handle missing fields gracefully
    search_params = {
        "api-version": "2023-11-01",
        "search": query,
        "$top": top,
        "$orderby": "published_date desc",
        "$select": "original_title,rewritten_title,source,published_date,was_rewritten,original_tone,confidence_score,rewrite_reason",
        "$count": "true"
    }
    
    # Add filters
    filters = []
    if filter_params:
        if filter_params.get('good_news_only'):
            filters.append("was_rewritten eq true")
        if filter_params.get('source'):
            filters.append(f"source eq '{filter_params['source']}'")
        if filter_params.get('tone'):
            filters.append(f"original_tone eq '{filter_params['tone']}'")
        if filter_params.get('min_confidence'):
            filters.append(f"confidence_score ge {filter_params['min_confidence']}")
        if filter_params.get('date_from'):
            filters.append(f"published_date ge {filter_params['date_from']}T00:00:00Z")
    
    if filters:
        search_params["$filter"] = " and ".join(filters)
    
    try:
        response = requests.get(search_url, headers=headers, params=search_params)
        if response.status_code == 200:
            return response.json()
        else:
            # Better error debugging
            st.error(f"❌ Search error: {response.status_code}")
            if response.status_code == 400:
                try:
                    error_detail = response.json()
                    st.error(f"Error details: {error_detail}")
                except:
                    st.error(f"Error response: {response.text}")
            return None
    except Exception as e:
        st.error(f"❌ Connection error: {str(e)}")
        return None

def get_sources():
    """Get list of available sources"""
    config = get_azure_config()
    search_url = f"{config['search_endpoint']}/indexes/{config['search_index']}/docs"
    headers = {
        "Content-Type": "application/json",
        "api-key": config['search_key']
    }
    
    search_params = {
        "api-version": "2023-11-01",
        "search": "*",
        "$top": 0,
        "facet": "source,count:50"
    }
    
    try:
        response = requests.get(search_url, headers=headers, params=search_params)
        if response.status_code == 200:
            data = response.json()
            if "@search.facets" in data and "source" in data["@search.facets"]:
                return [item["value"] for item in data["@search.facets"]["source"]]
        return []
    except:
        return []

def render_confidence_badge(confidence):
    """Render confidence score badge"""
    if confidence >= 80:
        css_class = "confidence-high"
        emoji = "🟢"
    elif confidence >= 60:
        css_class = "confidence-medium"
        emoji = "🟡"
    else:
        css_class = "confidence-low"
        emoji = "🔴"
    
    return f'<span class="confidence-badge {css_class}">{emoji} {confidence}%</span>'

def render_tone_badge(tone):
    """Render tone badge"""
    tone_colors = {
        "POSITIVE": "🟢",
        "NEUTRAL": "🟡", 
        "NEGATIVE": "🔴",
        "SENSATIONAL": "🟠"
    }
    emoji = tone_colors.get(tone, "⚪")
    return f"{emoji} {tone}"

# Main App Layout
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📰 NewsPerspective</h1>
        <p>Discover news with a positive perspective</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for filters
    with st.sidebar:
        st.header("🔍 Search & Filters")
        
        # Search query
        query = st.text_input("🔎 Search keywords", placeholder="Enter keywords to search...")
        
        # Good News Only toggle (prominent placement)
        st.markdown("### ✨ Content Filter")
        good_news_only = st.checkbox("🌟 **Good News Only**", value=False, help="Show only headlines that were rewritten for positivity")
        
        # Advanced filters in expander
        with st.expander("🔧 Advanced Filters"):
            sources = get_sources()
            selected_source = st.selectbox("📡 News Source", ["All Sources"] + sources)
            
            tone_filter = st.selectbox("🎭 Original Tone", ["All Tones", "POSITIVE", "NEUTRAL", "NEGATIVE", "SENSATIONAL"])
            
            min_confidence = st.slider("📊 Minimum Confidence", 0, 100, 60, help="Filter by AI confidence score")
            
            days_back = st.slider("📅 Days Back", 1, 30, 7, help="Show articles from last N days")
        
        # Search button
        search_clicked = st.button("🔍 **Search News**", type="primary", use_container_width=True)
    
    # Main content area
    if search_clicked or query:
        # Build filter parameters
        filter_params = {}
        if good_news_only:
            filter_params['good_news_only'] = True
        if selected_source != "All Sources":
            filter_params['source'] = selected_source
        if tone_filter != "All Tones":
            filter_params['tone'] = tone_filter
        if min_confidence > 0:
            filter_params['min_confidence'] = min_confidence
        
        # Date filter
        date_from = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        filter_params['date_from'] = date_from
        
        # Perform search
        with st.spinner("🔄 Searching for articles..."):
            results = search_articles(query or "*", filter_params, top=50)
        
        if results and results.get("value"):
            articles = results["value"]
            total_count = results.get("@odata.count", 0)
            
            # Results header with stats - using native Streamlit metrics
            col1, col2, col3, col4 = st.columns(4)
            
            rewritten_count = sum(1 for a in articles if a.get('was_rewritten'))
            avg_confidence = sum(a.get('confidence_score', 0) for a in articles) / len(articles) if articles else 0
            unique_sources = len(set(a.get('source', '') for a in articles))
            
            with col1:
                st.metric("📊 Total Articles", f"{total_count}")
            with col2:
                st.metric("✨ Improved Headlines", f"{rewritten_count}")
            with col3:
                st.metric("🎯 Avg Confidence", f"{avg_confidence:.0f}%")
            with col4:
                st.metric("📡 News Sources", f"{unique_sources}")
            
            st.markdown("---")
            
            # Display articles with clean Streamlit components
            for i, article in enumerate(articles):
                was_rewritten = article.get('was_rewritten', False)
                original_tone = article.get('original_tone', 'UNKNOWN')
                confidence = article.get('confidence_score', 0)
                
                # Format date
                pub_date = article.get('published_date', '')
                if pub_date:
                    try:
                        date_obj = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                        formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
                    except:
                        formatted_date = pub_date[:16]
                else:
                    formatted_date = "Unknown"
                
                # Create clean article container
                with st.container():
                    # Determine border color based on tone
                    if original_tone == "NEGATIVE":
                        border_color = "#dc3545"
                    elif original_tone == "NEUTRAL":
                        border_color = "#ffc107"
                    else:
                        border_color = "#28a745"
                    
                    # Article card with clean styling
                    st.markdown(f"""
                    <div style="
                        background: white;
                        padding: 1.5rem;
                        border-radius: 10px;
                        border-left: 4px solid {border_color};
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        margin-bottom: 1.5rem;
                    ">
                    """, unsafe_allow_html=True)
                    
                    # Header with source and metadata
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**📡 {article.get('source', 'Unknown Source')}** • 📅 {formatted_date}")
                    with col2:
                        # Tone and confidence badges
                        tone_emoji = {"POSITIVE": "🟢", "NEUTRAL": "🟡", "NEGATIVE": "🔴", "SENSATIONAL": "🟠"}.get(original_tone, "⚪")
                        conf_emoji = "🟢" if confidence >= 80 else "🟡" if confidence >= 60 else "🔴"
                        st.markdown(f"{tone_emoji} {original_tone} • {conf_emoji} {confidence}%")
                    
                    st.markdown("---")
                    
                    # Show positive rewrite FIRST and make it glow
                    if was_rewritten and article.get('rewritten_title'):
                        st.markdown("""
                        <div style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            padding: 1.5rem;
                            border-radius: 12px;
                            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
                            margin-bottom: 1rem;
                            border: 2px solid #fff;
                            animation: glow 2s ease-in-out infinite alternate;
                        ">
                        <style>
                        @keyframes glow {
                            from { box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3); }
                            to { box-shadow: 0 12px 40px rgba(102, 126, 234, 0.6); }
                        }
                        </style>
                        <h3 style="margin: 0; color: white;">✨ Positive Rewrite:</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"### **{article.get('rewritten_title', '')}**")
                        
                        # Original headline (smaller, below)
                        st.markdown("---")
                        st.markdown("**📰 Original Headline:**")
                        st.markdown(f"*{article.get('original_title', '')}*")
                        
                        # Reason (if exists)
                        if article.get('rewrite_reason'):
                            with st.expander("🔍 Why was this rewritten?"):
                                st.write(article.get('rewrite_reason', ''))
                    else:
                        # No rewrite - show original only
                        st.markdown("**📰 Original Headline:**")
                        st.markdown(f"### {article.get('original_title', '')}")
                    
                    # Read Full Article button
                    article_url = article.get('article_url', '')
                    if article_url:
                        st.markdown("---")
                        if st.button(f"📖 Read Full Article", key=f"read_{i}", help="Open original article in new tab"):
                            st.markdown(f'<a href="{article_url}" target="_blank">🔗 Open: {article_url}</a>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'🔗 **[Read Full Article]({article_url})**')
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
        else:
            st.info("🔍 No articles found matching your criteria. Try adjusting your filters or search terms.")
    
    else:
        # Welcome screen
        st.markdown("""
        ## 👋 Welcome to NewsPerspective!
        
        This app helps you discover news with a more positive perspective. Here's how to get started:
        
        ### 🌟 **Quick Start:**
        1. **Toggle "Good News Only"** to see headlines rewritten for positivity
        2. **Enter keywords** to search for specific topics
        3. **Use filters** to narrow down by source, tone, or date
        4. **Click "Search News"** to discover your personalized positive news feed
        
        ### ✨ **Features:**
        - 🔍 **Smart Search** - Find articles by keywords, source, or date
        - 🌟 **Positivity Filter** - View only improved headlines
        - 📊 **Confidence Scoring** - See how confident our AI is about improvements
        - 🎭 **Tone Analysis** - Understand the original tone of articles
        - 📱 **Clean Interface** - Minimalistic design focused on readability
        
        **Ready to explore positive news?** Use the sidebar to start searching! 📰✨
        """)

if __name__ == "__main__":
    main()

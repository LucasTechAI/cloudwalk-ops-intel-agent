from streamlit import (
    sidebar,
    session_state,
    rerun,
    title,
    info,
    markdown,
    button,
    select_slider,
    expander,
    cache_data,
)
from logging import Logger, basicConfig, getLogger, INFO
from pathlib import Path
from sys import path


basicConfig(
    level=INFO, format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
)
logger: Logger = getLogger(__name__)


root_path = Path(__file__).parent.parent.parent
path.append(str(root_path))
from src.dashboard.config.settings import DB_END_DATE, DB_START_DATE


def render_sidebar() -> int:
    """Renders the sidebar with configuration options"""
    logger.info("Rendering sidebar")
    with sidebar:
        title("⚙️ Configuration")

        if session_state.first_visit:
            info(
                """
            👋 **Welcome!**
            
            This dashboard provides comprehensive analytics for CloudWalk operations.
            
            Use the filters below to customize your analysis.
            """
            )

            if button("✓ Got it!", type="primary"):
                session_state.first_visit = False
                rerun()

        markdown("---")

        with expander("🔍 **Filters**", expanded=True):
            markdown("##### 📅 Time Period")

            markdown(f"📊 Available: {DB_START_DATE} to {DB_END_DATE}")

            days_filter = select_slider(
                "Days to analyze (from Mar 31):",
                options=[7, 15, 30, 60, 90],
                value=90,
                help="Retroactive analysis from March 31, 2025",
            )

        markdown("---")

        with expander("ℹ️ **About**"):
            markdown(
                """
                **CloudWalk Operations Intelligence**
                
                📊 Real-time analytics platform for transaction monitoring and business intelligence.
                
                **✨ Features:**
                - Live KPI tracking
                - Trend analysis & forecasting
                - AI-powered insights
                - Natural language queries
                
                **🛠️ Tech Stack:**
                ```
                Frontend    → Streamlit 1.28+
                Charts      → Plotly
                Data        → Pandas
                Database    → SQLite
                AI Engine   → LangChain + Llama 3.1
                ```
                
                ---
                
                **📅 Data Coverage:** Q1 2025 (Jan-Mar)  
                **📊 Dataset:** 292M+ transactions • R$ 38.8B TPV  
                **🔢 Version:** 2.0.0  
                
                ---
                
                **👨‍💻Developer:** Lucas Mendes Barbosa  
                **💻Repository:** [github.com/LucasTechAI](https://github.com/LucasTechAI/cloudwalk-ops-intel-agent)  
                **📧Contact:** [lucas.mendestech@gmail.com](mailto:lucas.mendestech@gmail.com)
                """
            )

        markdown("---")
        if button("🔄 Refresh Data", width="stretch"):
            cache_data.clear()
            rerun()
        logger.info(f"Selected days_filter: {days_filter}")
        return days_filter

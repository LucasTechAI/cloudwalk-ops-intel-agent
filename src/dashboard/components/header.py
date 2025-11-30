from streamlit import title, markdown, info, tabs, columns
from logging import Logger, basicConfig, getLogger, INFO

basicConfig(
    level=INFO, format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
)
logger: Logger = getLogger(__name__)


def render_header(days_filter: int) -> tuple:
    """Renders the dashboard header and main tabs"""
    logger.info("Rendering dashboard header")
    col_header1, col_header2 = columns([3, 1])

    with col_header1:
        title("📊 CloudWalk Operations Intelligence")
        markdown("*Real-time Analytics Dashboard • Q1 2025*")

    with col_header2:
        markdown("###  ")
        info(f"**Analysis Period**  \n📅 Last {days_filter} days")

    markdown("---")

    tab1, tab2, tab3, tab4 = tabs(
        ["📊 Overview", "📈 Trends & Analysis", "🔍 Deep Dive", "💬 AI Assistant"]
    )
    logger.info("Main tabs rendered")
    return tab1, tab2, tab3, tab4

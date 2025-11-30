from streamlit import set_page_config, markdown, session_state, warning
from logging import Logger, basicConfig, getLogger, INFO
from pathlib import Path
from sys import path

basicConfig(
    level=INFO, format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
)
logger: Logger = getLogger(__name__)


root_path = Path(__file__).parent.parent.parent
path.append(str(root_path))

from src.dashboard.config.settings import (
    INITIAL_SIDEBAR_STATE,
    LAYOUT,
    PAGE_ICON,
    PAGE_TITLE,
)
from src.dashboard.components.deep_dive import render_deep_dive_page
from src.dashboard.components.assistant import render_assistant_page
from src.dashboard.components.overview import render_overview_page
from src.dashboard.components.trends import render_trends_page
from src.dashboard.components.sidebar import render_sidebar
from src.dashboard.components.header import render_header
from src.dashboard.utils.loader import init_db


def inicialize_session() -> None:
    """
    Innit Streamlit session with default values
    """
    logger.info("Initializing Streamlit session")
    set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=LAYOUT,
        initial_sidebar_state=INITIAL_SIDEBAR_STATE,
    )

    theme_path = Path(__file__).parent / "styles" / "theme.html"

    if theme_path.exists():
        with open(theme_path, "r", encoding="utf-8") as f:
            markdown(f.read(), unsafe_allow_html=True)
    else:
        logger.warning(f"Theme file not found: {theme_path}")
        warning(f"⚠️ Theme file not found: {theme_path}")

    if "first_visit" not in session_state:
        session_state.first_visit = True


def main() -> None:
    """Main function to run the Streamlit dashboard"""
    logger.info("Starting Streamlit dashboard")
    db_manager = init_db()

    inicialize_session()

    days_filter = render_sidebar()

    tab1, tab2, tab3, tab4 = render_header(days_filter)

    with tab1:
        render_overview_page(db_manager, days_filter)
    with tab2:
        render_trends_page(db_manager, days_filter)
    with tab3:
        render_deep_dive_page(db_manager)
    with tab4:
        render_assistant_page(db_manager)


if __name__ == "__main__":
    main()

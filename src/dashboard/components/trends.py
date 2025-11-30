from streamlit import header, columns, plotly_chart, error, subheader, markdown
from logging import Logger, basicConfig, getLogger, INFO
from plotly.graph_objects import Scatter, Figure, Bar
from plotly.express import bar, line
from pathlib import Path
from sys import path


basicConfig(
    level=INFO, format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
)
logger: Logger = getLogger(__name__)


root_path = Path(__file__).parent.parent.parent
path.append(str(root_path))

from src.dashboard.utils.loader import (
    load_daily_trends,
    load_product_comparison,
    load_weekday_analysis,
)
from src.dashboard.utils.charts import apply_chart_theme
from src.utils.sqlite_manager import SqliteManager


def render_trends_page(db_manager: SqliteManager, days_filter: int) -> None:
    """Renders the Trends & Performance Analysis page"""
    logger.info("Rendering Trends & Performance Analysis page")
    header("📈 Trends & Performance Analysis")
    try:
        logger.info("Loading trends data")
        daily_trends = load_daily_trends(db_manager, days=days_filter)

        if not daily_trends.empty:
            col_t1, col_t2 = columns(2)

            with col_t1:
                subheader("💰 TPV Evolution")

                fig_tpv = Figure()
                fig_tpv.add_trace(
                    Scatter(
                        x=daily_trends["day"],
                        y=daily_trends["tpv"],
                        mode="lines+markers",
                        name="Daily TPV",
                        line=dict(color="#1f77b4", width=3),
                        fill="tozeroy",
                        fillcolor="rgba(31, 119, 180, 0.2)",
                        marker=dict(size=6),
                    )
                )
                fig_tpv.add_trace(
                    Scatter(
                        x=daily_trends["day"],
                        y=daily_trends["moving_avg_7d"],
                        mode="lines",
                        name="7-day Moving Avg",
                        line=dict(color="#ff7f0e", width=2, dash="dash"),
                    )
                )

                fig_tpv = apply_chart_theme(fig_tpv, "")
                fig_tpv.update_xaxes(title="Date")
                fig_tpv.update_yaxes(title="TPV (R$)")

                plotly_chart(fig_tpv, width="stretch")

            with col_t2:
                subheader(f"📊 D-{days_filter} Variation (%)")

                colors = [
                    "#2ecc71" if x > 0 else "#e74c3c"
                    for x in daily_trends["var_d7_pct"]
                ]

                fig_var = Figure()
                fig_var.add_trace(
                    Bar(
                        x=daily_trends["day"],
                        y=daily_trends["var_d7_pct"],
                        marker_color=colors,
                        name=f"D-{days_filter} Variation",
                        hovertemplate="<b>%{x}</b><br>Variation: %{y:.2f}%<extra></extra>",
                    )
                )
                fig_var.add_hline(
                    y=0, line_dash="dash", line_color="gray", line_width=2
                )

                fig_var = apply_chart_theme(fig_var, "")
                fig_var.update_xaxes(title="Date")
                fig_var.update_yaxes(title="Variation (%)")

                plotly_chart(fig_var, width="stretch")

            markdown("---")

            col_t3, col_t4 = columns(2)

            with col_t3:
                subheader("📦 Product Performance")

                product_comp = load_product_comparison(db_manager)

                if not product_comp.empty:
                    fig_prod = bar(
                        product_comp.head(10),
                        x="product",
                        y="tpv",
                        color="entity",
                        title="",
                        labels={
                            "tpv": "TPV (R$)",
                            "product": "Product",
                            "entity": "Entity",
                        },
                        color_discrete_map={"PF": "#1f77b4", "PJ": "#44a5ea"},
                    )
                    fig_prod = apply_chart_theme(fig_prod, "")
                    plotly_chart(fig_prod, width="stretch")

            with col_t4:
                subheader("📅 Weekday Performance")

                weekday_analysis = load_weekday_analysis(db_manager)

                if not weekday_analysis.empty:
                    fig_week = line(
                        weekday_analysis,
                        x="weekday",
                        y="avg_daily_tpv",
                        markers=True,
                        title="",
                        labels={
                            "avg_daily_tpv": "Daily Avg TPV (R$)",
                            "weekday": "Weekday",
                        },
                    )
                    fig_week.update_traces(
                        line=dict(width=3, color="#1f77b4"), marker=dict(size=10)
                    )
                    fig_week = apply_chart_theme(fig_week, "")
                    plotly_chart(fig_week, width="stretch")

    except Exception as e:
        logger.error(f"Error loading trends: {e}")
        error(f"❌ Error loading trends: {str(e)}")

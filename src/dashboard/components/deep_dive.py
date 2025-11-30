from streamlit import (
    header,
    tabs,
    subheader,
    columns,
    plotly_chart,
    markdown,
    metric,
    error,
    dataframe,
)
from logging import Logger, basicConfig, getLogger, INFO
from plotly.graph_objects import Figure, Bar, Scatter
from plotly.express import sunburst, treemap
from pathlib import Path
from sys import path


basicConfig(
    level=INFO, format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
)
logger: Logger = getLogger(__name__)

root_path = Path(__file__).parent.parent.parent
path.append(str(root_path))

from src.dashboard.utils.loader import (
    load_anticipation_analysis,
    load_segmentation,
    load_installments_analysis,
)
from src.dashboard.utils.charts import apply_chart_theme
from src.utils.sqlite_manager import SqliteManager


def render_deep_dive_page(db_manager: SqliteManager) -> None:
    """Renders the Deep Dive Analysis page"""
    logger.info("Rendering Deep Dive Analysis page")
    header("🔍 Deep Dive Analysis")

    subtab1, subtab2, subtab3 = tabs(
        ["💳 Payment Methods", "📊 Segmentation", "📈 Installments"]
    )

    with subtab1:
        subheader("Anticipation Methods Distribution")

        try:
            logger.info("Loading anticipation analysis data")
            anticipation = load_anticipation_analysis(db_manager)

            if not anticipation.empty:
                col_ant1, col_ant2 = columns([2, 1])

                with col_ant1:
                    fig_sun = sunburst(
                        anticipation,
                        path=["entity", "anticipation_method"],
                        values="tpv",
                        title="",
                        color="tpv",
                        color_continuous_scale="Teal",
                    )
                    fig_sun.update_traces(
                        hovertemplate="<b>%{label}</b><br>"
                        + "TPV: R$ %{value:,.2f}<br>"
                        + "Share: %{percentParent:.2%}<br>"
                        + "<extra></extra>"
                    )
                    fig_sun = apply_chart_theme(fig_sun, "", height=500)
                    plotly_chart(fig_sun, width="stretch")

                with col_ant2:
                    markdown("##### 📊 Summary by Entity")

                    summary = (
                        anticipation.groupby("entity")
                        .agg({"tpv": "sum", "total_transactions": "sum"})
                        .reset_index()
                    )

                    for _, row in summary.iterrows():
                        metric(
                            label=f"{row['entity'].title()}",
                            value=f"R$ {row['tpv']:,.0f}",
                            delta=f"{row['total_transactions']:,.0f} trans",
                        )

        except Exception as e:
            logger.error(f"Error loading anticipation data: {e}")
            error(f"❌ Error loading anticipation data: {str(e)}")

    with subtab2:
        subheader("Transaction Segmentation")

        try:
            logger.info("Loading segmentation data")
            segmentation = load_segmentation(db_manager)

            if not segmentation.empty:
                fig_tree = treemap(
                    segmentation,
                    path=["entity", "product", "payment_method"],
                    values="tpv",
                    title="",
                    color="tpv_pct_of_total",
                    color_continuous_scale="Teal",
                )
                fig_tree = apply_chart_theme(fig_tree, "", height=600)
                plotly_chart(fig_tree, width="stretch")

                markdown("##### 📋 Detailed Breakdown")
                dataframe(
                    segmentation.style.format(
                        {
                            "tpv": "R$ {:,.2f}",
                            "total_transactions": "{:,.0f}",
                            "avg_ticket": "R$ {:,.2f}",
                            "tpv_pct_of_total": "{:.2f}%",
                        }
                    ),
                    width="stretch",
                    height=400,
                )

        except Exception as e:
            logger.error(f"Error loading segmentation: {e}")
            error(f"❌ Error loading segmentation: {str(e)}")

    with subtab3:
        subheader("Installments Analysis")

        try:
            logger.info("Loading installments analysis data")
            installments = load_installments_analysis(db_manager)

            if not installments.empty:
                fig_inst = Figure()

                fig_inst.add_trace(
                    Bar(
                        x=installments["installments"],
                        y=installments["tpv"],
                        name="TPV",
                        yaxis="y",
                        marker_color="#3498db",
                        hovertemplate="<b>%{x}x</b><br>TPV: R$ %{y:,.2f}<extra></extra>",
                    )
                )

                fig_inst.add_trace(
                    Scatter(
                        x=installments["installments"],
                        y=installments["avg_ticket"],
                        name="Avg Ticket",
                        yaxis="y2",
                        mode="lines+markers",
                        line=dict(color="#e74c3c", width=3),
                        marker=dict(size=10),
                        hovertemplate="<b>%{x}x</b><br>Avg: R$ %{y:,.2f}<extra></extra>",
                    )
                )

                fig_inst = apply_chart_theme(fig_inst, "", height=500)
                fig_inst.update_layout(
                    xaxis=dict(title="Number of Installments"),
                    yaxis=dict(title="TPV (R$)", side="left"),
                    yaxis2=dict(title="Avg Ticket (R$)", overlaying="y", side="right"),
                )

                plotly_chart(fig_inst, width="stretch")

                col_inst1, col_inst2, col_inst3 = columns(3)

                with col_inst1:
                    most_used = installments.loc[installments["transactions"].idxmax()]
                    metric(
                        "Most Used",
                        f"{int(most_used['installments'])}x",
                        f"{most_used['transactions']:,.0f} trans",
                    )

                with col_inst2:
                    highest_tpv = installments.loc[installments["tpv"].idxmax()]
                    metric(
                        "Highest TPV",
                        f"{int(highest_tpv['installments'])}x",
                        f"R$ {highest_tpv['tpv']:,.0f}",
                    )

                with col_inst3:
                    highest_ticket = installments.loc[
                        installments["avg_ticket"].idxmax()
                    ]
                    metric(
                        "Highest Avg Ticket",
                        f"{int(highest_ticket['installments'])}x",
                        f"R$ {highest_ticket['avg_ticket']:,.2f}",
                    )

        except Exception as e:
            error(f"❌ Error loading installments: {str(e)}")
            logger.error(f"Error loading installments analysis: {e}")

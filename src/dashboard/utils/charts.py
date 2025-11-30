from streamlit import columns, container, metric, plotly_chart, markdown
from logging import Logger, basicConfig, getLogger, INFO
from plotly.graph_objects import Figure, Scatter
from pathlib import Path
from sys import path


basicConfig(
    level=INFO, format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
)
logger: Logger = getLogger(__name__)


root_path = Path(__file__).parent.parent.parent
path.append(str(root_path))


def apply_chart_theme(fig: Figure, title: str = "", height: int = 400) -> Figure:
    """Applies a custom theme to Plotly charts"""
    logger.info("Applying chart theme")
    fig.update_layout(
        title={
            "text": title,
            "font": {"size": 18, "color": "#2c3e50", "family": "Arial, sans-serif"},
            "x": 0.5,
            "xanchor": "center",
            "y": 0.95,
            "yanchor": "top",
        },
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
        hovermode="closest",
        margin=dict(l=60, r=60, t=80, b=60),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
        ),
        height=height,
    )

    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.08)",
        showline=True,
        linewidth=1,
        linecolor="rgba(0,0,0,0.2)",
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.08)",
        showline=True,
        linewidth=1,
        linecolor="rgba(0,0,0,0.2)",
    )
    logger.info("Chart theme applied successfully")
    return fig


def metric_with_sparkline(
    label: str, value: float, trend_data=None, delta=None, help_text=None
) -> None:
    """Creates a metric with a mini trend chart"""
    logger.info(f"Creating metric with sparkline for {label}")
    cols = columns([3, 1]) if trend_data is not None else [container()]

    with cols[0]:
        metric(label=label, value=value, delta=delta, help=help_text)

    if trend_data is not None and len(trend_data) > 0:
        with cols[1]:
            fig = Figure()
            fig.add_trace(
                Scatter(
                    y=trend_data,
                    mode="lines",
                    line=dict(color="#1f77b4", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(31, 119, 180, 0.2)",
                )
            )
            fig.update_layout(
                height=60,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def alert_card(
    level: str, title: str, message: str, metric_value: float = None
) -> None:
    """Creates a styled alert card"""
    logger.info(f"Creating alert card: {level} - {title}")
    icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}

    classes = {
        "CRITICAL": "alert-critical",
        "HIGH": "alert-high",
        "MEDIUM": "alert-medium",
        "LOW": "alert-low",
    }

    metric_html = (
        f'<div style="margin-top: 8px; font-size: 1.2rem; font-weight: 700; color: #2c3e50;">R$ {metric_value:,.2f}</div>'
        if metric_value
        else ""
    )

    markdown(
        f"""
        <div class="alert-card {classes.get(level, 'alert-medium')}">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 1.5rem;">{icons.get(level, '⚪')}</span>
                <div style="flex: 1;">
                    <div style="font-weight: 700; font-size: 1rem; margin-bottom: 4px; color: #2c3e50;">
                        {level}: {title}
                    </div>
                    <div style="color: #7f8c8d; font-size: 0.875rem;">
                        {message}
                    </div>
                    {metric_html}
                </div>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    logger.info("Alert card created successfully")

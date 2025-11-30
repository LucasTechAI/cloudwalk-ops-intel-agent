from streamlit import header, columns, markdown, metric, subheader, error, success
from logging import Logger, basicConfig, getLogger, INFO
from pandas import DataFrame
from pathlib import Path
from sys import path

basicConfig(
    level=INFO, format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
)
logger: Logger = getLogger(__name__)


root_path = Path(__file__).parent.parent.parent
path.append(str(root_path))

from src.dashboard.utils.loader import load_overall_kpis, load_daily_trends, load_alerts
from src.dashboard.utils.charts import metric_with_sparkline, alert_card
from src.utils.sqlite_manager import SqliteManager


def render_overview_page(db_manager: SqliteManager, days_filter: int) -> None:
    """Renders the Key Performance Indicators overview page"""
    logger.info("Rendering Overview page")
    header("Key Performance Indicators")

    try:
        logger.info("Loading overview data")
        kpis = load_overall_kpis(db_manager)
        daily_trends = load_daily_trends(db_manager, days=days_filter)

        if not kpis.empty:
            col1, col2, col3 = columns(3)

            with col1:
                trend_data = (
                    daily_trends["tpv"].tail(30).tolist()
                    if not daily_trends.empty
                    else None
                )
                metric_with_sparkline(
                    label="💰 Total TPV",
                    value=f"R$ {kpis['total_tpv'].iloc[0]:,.0f}",
                    trend_data=trend_data,
                    help_text="Total Payment Volume - Sum of all transactions",
                )

            with col2:
                trend_data = (
                    daily_trends["transactions"].tail(30).tolist()
                    if not daily_trends.empty
                    else None
                )
                metric_with_sparkline(
                    label="🔄 Transactions",
                    value=f"{kpis['total_transactions'].iloc[0]:,.0f}",
                    trend_data=trend_data,
                    help_text="Total number of processed transactions",
                )

            with col3:
                trend_data = (
                    daily_trends["avg_ticket"].tail(30).tolist()
                    if not daily_trends.empty
                    else None
                )
                metric_with_sparkline(
                    label="🎫 Avg Ticket",
                    value=f"R$ {kpis['avg_ticket'].iloc[0]:,.2f}",
                    trend_data=trend_data,
                    help_text="Average transaction value",
                )

            markdown("---")

            subheader(f"📊 Period Summary - Last {days_filter} Days")

            if not daily_trends.empty:
                col_stats1, col_stats2, col_stats3, col_stats4 = columns(4)

                total_tpv = daily_trends["tpv"].sum()
                total_trans = daily_trends["transactions"].sum()
                avg_ticket_period = total_tpv / total_trans if total_trans > 0 else 0
                last_var = daily_trends["var_d7_pct"].iloc[-1]

                with col_stats1:
                    metric(
                        "Period TPV",
                        f"R$ {total_tpv:,.0f}",
                        help=f"Total TPV in last {days_filter} days",
                    )

                with col_stats2:
                    metric(
                        "Period Transactions",
                        f"{total_trans:,.0f}",
                        help=f"Transactions in last {days_filter} days",
                    )

                with col_stats3:
                    metric(
                        "Period Avg Ticket",
                        f"R$ {avg_ticket_period:,.2f}",
                        help=f"Average ticket in last {days_filter} days",
                    )

                with col_stats4:
                    delta_color = "normal" if last_var >= 0 else "inverse"
                    metric(
                        "Last D-7 Var",
                        f"{last_var:+.2f}%",
                        delta=f"{last_var:.2f}%",
                        help="Latest 7-day variation",
                    )

            subheader(f"🚨 Critical Alerts - Last {days_filter} Days")

            alerts = load_alerts(db_manager, days=days_filter)
            critical_alerts = (
                alerts[alerts["severity_score"] >= 4]
                if not alerts.empty
                else DataFrame()
            )

            if not critical_alerts.empty:
                for _, alert in critical_alerts.head(5).iterrows():
                    alert_card(
                        level=alert["alert_level"],
                        title=f"{alert['product']} • {alert['entity']}",
                        message=alert["alert_message"],
                        metric_value=alert["tpv"],
                    )
            else:
                success("✅ No critical alerts in this period!")

            markdown("---")

    except Exception as e:
        error(f"❌ Error loading overview data: {str(e)}")


from src.dashboard.utils.loader import load_product_comparison, load_weekday_analysis

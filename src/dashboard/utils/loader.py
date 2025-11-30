from logging import Logger, basicConfig, getLogger, INFO
from streamlit import cache_data, cache_resource
from pandas import DataFrame
from pathlib import Path
from sys import path

basicConfig(
    level=INFO, format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
)
logger: Logger = getLogger(__name__)


root_path = Path(__file__).parent.parent.parent
path.append(str(root_path))

from src.dashboard.config.settings import DB_END_DATE
from src.utils.sqlite_manager import SqliteManager


@cache_resource
def init_db() -> SqliteManager:
    """
    Innit the database connection
    """
    logger.info("Initializing database connection")
    db_manager = SqliteManager()
    return db_manager


@cache_data(ttl=300)
def load_overall_kpis(_db_manager: SqliteManager) -> DataFrame:
    """
    Load overall KPIs
    """
    logger.info("Loading overall KPIs")
    query = """
    SELECT 
        SUM(tpv) as total_tpv,
        SUM(total_transactions) as total_transactions,
        SUM(total_merchants) as total_merchants,
        AVG(average_ticket) as avg_ticket,
        MAX(day) as last_update
    FROM v_kpi
    """
    return _db_manager.select_query(query)


@cache_data(ttl=300)
def load_daily_trends(_db_manager: SqliteManager, days: int = 90) -> DataFrame:
    """
    Load daily trends for KPIs
    """
    logger.info(f"Loading daily trends for the last {days} days")
    query = f"""
    SELECT 
        day,
        SUM(tpv) as tpv,
        SUM(total_transactions) as transactions,
        AVG(avg_ticket) as avg_ticket,
        AVG(var_d7_pct) as var_d7_pct,
        AVG(avg_7d) as moving_avg_7d
    FROM v_daily_kpis
    WHERE day >= date('{DB_END_DATE}', '-{days} days')
      AND day <= '{DB_END_DATE}'
    GROUP BY day
    ORDER BY day
    """
    return _db_manager.select_query(query)


@cache_data(ttl=300)
def load_product_comparison(_db_manager: SqliteManager) -> DataFrame:
    """
    Load product comparison
    """
    logger.info("Loading product comparison data")
    query = """
    SELECT 
        product,
        entity,
        tpv,
        total_transactions,
        avg_ticket,
        tpv_pct_of_total,
        days_active
    FROM v_product_comparison
    ORDER BY tpv DESC
    """
    return _db_manager.select_query(query)


@cache_data(ttl=300)
def load_weekday_analysis(_db_manager: SqliteManager) -> DataFrame:
    """
    Load weekday analysis
    """
    logger.info("Loading weekday analysis data")
    query = """
    SELECT 
        weekday,
        weekday_num,
        SUM(tpv) as tpv,
        SUM(total_transactions) as transactions,
        AVG(avg_ticket) as avg_ticket,
        AVG(avg_daily_tpv) as avg_daily_tpv
    FROM v_weekday_analysis
    GROUP BY weekday, weekday_num
    ORDER BY weekday_num
    """
    return _db_manager.select_query(query)


@cache_data(ttl=300)
def load_alerts(_db_manager: SqliteManager, days: int = 90) -> DataFrame:
    """
    Loads alerts data
    """
    logger.info(f"Loading alerts data for the last {days} days")
    query = f"""
    SELECT 
        day,
        entity,
        product,
        payment_method,
        tpv,
        alert_level,
        alert_message,
        severity_score,
        var_d7_pct,
        var_vs_14d_pct
    FROM v_alerts
    WHERE day >= date('{DB_END_DATE}', '-{days} days')
      AND day <= '{DB_END_DATE}'
    ORDER BY severity_score DESC, day DESC
    LIMIT 20
    """
    return _db_manager.select_query(query)


@cache_data(ttl=300)
def load_segmentation(_db_manager: SqliteManager) -> DataFrame:
    """
    Load segmentation analysis
    """
    logger.info("Loading segmentation analysis data")
    query = """
    SELECT 
        entity,
        product,
        payment_method,
        tpv,
        total_transactions,
        avg_ticket,
        tpv_pct_of_total
    FROM v_segmentation
    ORDER BY tpv DESC
    LIMIT 15
    """
    return _db_manager.select_query(query)


@cache_data(ttl=300)
def load_anticipation_analysis(_db_manager: SqliteManager) -> DataFrame:
    """
    Load anticipation method analysis
    """
    logger.info("Loading anticipation method analysis data")
    query = """
    SELECT 
        entity,
        anticipation_method,
        tpv,
        total_transactions,
        tpv_pct_by_entity,
        transactions_pct_by_entity
    FROM v_anticipation_analysis
    ORDER BY entity, tpv DESC
    """
    return _db_manager.select_query(query)


@cache_data(ttl=300)
def load_installments_analysis(_db_manager: SqliteManager) -> DataFrame:
    """
    Load installments analysis
    """
    logger.info("Loading installments analysis data")
    query = """
    SELECT 
        installments,
        SUM(tpv) as tpv,
        SUM(total_transactions) as transactions,
        AVG(avg_ticket) as avg_ticket,
        AVG(tpv_pct) as tpv_pct
    FROM v_installments_analysis
    GROUP BY installments
    ORDER BY installments
    """
    return _db_manager.select_query(query)

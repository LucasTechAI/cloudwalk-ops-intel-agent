from logging import Logger, getLogger, basicConfig, INFO
from sqlite3 import Error
from pathlib import Path
from sys import path as sys_path

project_root = Path(__file__).resolve().parent.parent
sys_path.insert(0, str(project_root))

from src.utils.sqlite_manager import EXPECTED_COLUMNS, SqliteManager

CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS test_operations (
        day TEXT,
        entity TEXT,
        product TEXT,
        price_tier TEXT,
        anticipation_method TEXT,
        payment_method TEXT,
        installments INTEGER,
        amount_transacted REAL,
        quantity_transactions INTEGER,
        quantity_of_merchants INTEGER
    );
"""

SELECT_QUERY_SQL = "SELECT * FROM test_operations;"
INSERT_QUERY_SQL = """
    INSERT INTO test_operations (
        day, entity, product, price_tier,
        anticipation_method, payment_method, installments,
        amount_transacted, quantity_transactions, quantity_of_merchants
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

SAMPLES_INSERT = [
    (
        "2025-01-01",
        "StoreX",
        "ProductA",
        "Tier1",
        "MethodA",
        "Credit",
        3,
        200.50,
        10,
        2,
    ),
    (
        "2025-01-02",
        "StoreY",
        "ProductB",
        "Tier2",
        "MethodB",
        "Debit",
        1,
        500.00,
        20,
        5,
    ),
]

basicConfig(
    level=INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s",
)
logger: Logger = getLogger(__name__)


def test_connection() -> None:
    """Test database connection."""
    try:
        with SqliteManager() as db:
            assert db.conn is not None, "Connection object is None"
            logger.info("Connection test passed")
    except (Error, AssertionError) as e:
        logger.error(f"Connection test failed: {e}")
        raise


def test_create_table() -> None:
    """Create a test table."""
    try:
        with SqliteManager() as db:
            db.conn.execute(CREATE_TABLE_SQL)
            db.conn.commit()
            logger.info("Test table created successfully")
    except Error as e:
        logger.error(f"Error creating table: {e}")
        raise


def test_insert_sample_data() -> None:
    """Insert sample data into the test_operations table."""
    try:
        with SqliteManager() as db:
            db.conn.executemany(INSERT_QUERY_SQL, SAMPLES_INSERT)
            db.conn.commit()
            logger.info(f"{len(SAMPLES_INSERT)} sample records inserted")
    except Error as e:
        logger.error(f"Error inserting sample data: {e}")
        raise


def test_query_data() -> None:
    """Test querying data from the test_operations table."""
    try:
        with SqliteManager() as db:
            df = db.select_query(SELECT_QUERY_SQL)

        logger.info(f"Query executed successfully. Retrieved {len(df)} rows")
        logger.info(f"Data preview:\n{df}")
    except Error as e:
        logger.error(f"Error querying data: {e}")
        raise


def test_validate_columns() -> None:
    """Validate if the columns match EXPECTED_COLUMNS."""
    try:
        with SqliteManager() as db:
            df = db.select_query("PRAGMA table_info(test_operations)")

        db_columns = df["name"].tolist()

        if db_columns == EXPECTED_COLUMNS:
            logger.info("Column validation passed")
        else:
            logger.warning("Column mismatch detected")
            logger.warning(f"Expected: {EXPECTED_COLUMNS}")
            logger.warning(f"Found: {db_columns}")
    except Error as e:
        logger.error(f"Error validating columns: {e}")
        raise


def delete_test_table() -> None:
    """Delete the test_operations table."""
    try:
        with SqliteManager() as db:
            db.delete_tables(["test_operations"])
            logger.info("Test table deleted successfully")
    except Error as e:
        logger.error(f"Error deleting test table: {e}")
        raise


def main() -> None:
    """Run all tests."""
    logger.info("=" * 50)
    logger.info("STARTING TESTS")
    logger.info("=" * 50)

    tests = [
        test_connection,
        test_create_table,
        test_insert_sample_data,
        test_query_data,
        test_validate_columns,
        delete_test_table,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception:
            failed += 1

    logger.info("=" * 50)
    logger.info(f"TESTS COMPLETED: {passed} passed, {failed} failed")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()

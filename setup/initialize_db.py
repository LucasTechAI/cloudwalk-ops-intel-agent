from logging import Logger, getLogger, basicConfig, INFO
from sys import exit, path
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
path.insert(0, str(project_root))

from src.utils.sqlite_manager import SqliteManager

QUERY_SELECT_PREVIEW = "SELECT name FROM sqlite_master WHERE type='table';"
QUERY_SELECT_DATA = "SELECT * FROM transactions LIMIT 5;"


def setup_logging() -> Logger:
    """Configures and returns the logger."""
    basicConfig(
        level=INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s",
    )
    return getLogger(__name__)


def main() -> None:
    """
    Main function to initialize the database, create the schema,
    load data, and create views.
    """
    logger: Logger = setup_logging()

    try:
        logger.info("Starting database configuration and loading routine...")

        with SqliteManager() as db:
            logger.info(
                "Database connection established. Optimizing initial structure..."
            )

            logger.info("Creating database schema (tables) from schema.sql...")
            db.create_schema()

            logger.info("Loading data from CSV files into the tables...")
            db.load_data_from_csv()

            logger.info("Creating views to facilitate analytical queries...")
            db.create_views()

            logger.info("Verification: Listing all created views...")
            views_df = db.select_query(
                "SELECT name FROM sqlite_master WHERE type='view';"
            )
            logger.info(f"Views created:\n{views_df['name'].tolist()}")

            logger.info(
                "Optimizing and cleaning up the database for better performance..."
            )
            db.optimize_database()

            logger.info("Verification: Selecting existing tables...")
            tables_df = db.select_query(QUERY_SELECT_PREVIEW)
            logger.info(f"Tables created:\n{tables_df['name'].tolist()}")

            logger.info(
                "Verification: Preview of the first 5 rows from the 'transactions' table..."
            )
            data_df = db.select_query(QUERY_SELECT_DATA)
            logger.info(f"\n--- Data Preview ---\n{data_df}\n--------------------")

        logger.info(
            "Database configuration successfully completed and connection closed."
        )

    except Exception as e:
        logger.error("FATAL ERROR during database setup.", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()

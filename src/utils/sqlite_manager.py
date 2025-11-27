from pandas import DataFrame, read_csv, to_datetime, read_sql_query
from logging import Logger, basicConfig, getLogger, INFO
from sqlite3 import Connection, connect, Error
from dotenv import load_dotenv
from pathlib import Path
from os import getenv


load_dotenv()

basicConfig(
    level=INFO, format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
)
logger: Logger = getLogger(__name__)

DB_SCHEMA_PATH: str = getenv("DB_SCHEMA_PATH")
PATH_OPERATIONS_ANALYST_DATA: str = getenv("PATH_OPERATIONS_ANALYST_DATA")
DB_PATH: str = getenv("DB_PATH")
DB_VIEWS_PATH: str = getenv("DB_VIEWS_PATH")

EXPECTED_COLUMNS = [
    "day",
    "entity",
    "product",
    "price_tier",
    "anticipation_method",
    "payment_method",
    "installments",
    "amount_transacted",
    "quantity_transactions",
    "quantity_of_merchants",
]


class SqliteManager:
    def __init__(self, db_path: str = None) -> None:
        """
        Constructs a SqliteManager object.
        Args:
            db_path (str, optional): Path to the SQLite database file. Defaults to None, which uses the DB_PATH from environment variables.
        """
        self.db_path: str = db_path or DB_PATH
        self.conn: Connection = None

    def __enter__(self) -> "SqliteManager":
        """
        Context manager entry method.
        Returns:
            SqliteManager: The SqliteManager instance with an active database connection.
        """
        self.conn = self.connect()
        return self

    def __exit__(self, exc_type: type, exc_value: Exception, traceback: any) -> None:
        """
        Context manager exit method. Closes the database connection.
        Args:
            exc_type (type): Exception type, if any.
            exc_value (Exception): Exception value, if any.
            traceback (any): Traceback object, if any.
        """
        self.close()
        return None

    def connect(self) -> Connection:
        """
        Establishes a connection to the SQLite database.
        Returns:
            Connection: SQLite database connection object.
        """
        try:
            self.conn: Connection = connect(self.db_path)
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.conn.execute("PRAGMA foreign_keys=ON")
            return self.conn
        except Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def create_schema(self) -> None:
        """
        Creates the database schema from the provided SQL file.
        """
        try:
            logger.info("Creating database schema...")
            self.conn.executescript(Path(DB_SCHEMA_PATH).read_text())
            self.conn.commit()
            logger.info("Schema created successfully.")
        except Error as e:
            logger.error(f"Error creating schema: {e}")
            raise

    def create_views(self) -> None:
        """
        Creates database views from the provided SQL file.
        """
        try:
            logger.info("Creating database views...")
            self.conn.executescript(Path(DB_VIEWS_PATH).read_text())
            self.conn.commit()
            logger.info("Views created successfully.")
        except Error as e:
            logger.error(f"Error creating views: {e}")
            raise

    def delete_tables(self, table_names: list) -> None:
        """
        Deletes specified tables from the database.
        Args:
            table_names (list): List of table names to delete.
        """
        try:
            for table in table_names:
                logger.info(f"Deleting table: {table}...")
                self.conn.execute(f"DROP TABLE IF EXISTS {table};")
            self.conn.commit()
            logger.info("Tables deleted successfully.")
        except Error as e:
            logger.error(f"Error deleting tables: {e}")
            raise

    def __batch_insert(self, df_clean: DataFrame, total: int, batch_size: int) -> None:
        """
        Insert data into the database in batches.
        Args:
            df_clean (DataFrame): Cleaned DataFrame to insert.
            total (int): Total number of rows to insert.
            batch_size (int): Number of rows per batch.
        """
        try:
            for i in range(0, total, batch_size):
                batch = df_clean.iloc[i : i + batch_size]
                batch.to_sql(
                    "transactions",
                    self.conn,
                    if_exists="append",
                    index=False,
                    method="multi",
                )

                conditional_log: bool = (i // batch_size + 1) % 10 == 0

                if conditional_log:
                    logger.info(f"Progress: {i+len(batch)}/{total} rows inserted")
        except Exception as e:
            logger.error(f"Error during batch insert: {e}", exc_info=True)
            raise

    def load_data_from_csv(self, batch_size: int = 5000) -> None:
        try:
            logger.info(f"Initial load from CSV: {PATH_OPERATIONS_ANALYST_DATA}")

            df: DataFrame = read_csv(PATH_OPERATIONS_ANALYST_DATA)
            logger.info(f"DataFrame loaded: {len(df)} rows")
            logger.info(f"Dtypes:\n{df.dtypes}")

            missing_cols: set = set(EXPECTED_COLUMNS) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing columns in CSV: {missing_cols}")

            df_clean: DataFrame = df[EXPECTED_COLUMNS].copy()
            df_clean["day"] = to_datetime(df_clean["day"]).dt.strftime("%Y-%m-%d")

            total_rows: int = len(df_clean)
            num_batches: int = (total_rows + batch_size - 1) // batch_size

            logger.info(f"Inserting {total_rows} rows in {num_batches} batches...")
            self.__batch_insert(df_clean, total_rows, batch_size)
            self.conn.commit()

            logger.info(f"✓ Load complete! {total_rows} rows inserted.")
        except Exception as e:
            logger.error(f"Error loading data from CSV: {e}", exc_info=True)
            raise

    def optimize_database(self) -> None:
        """
        Optimizes the SQLite database using ANALYZE and VACUUM.
        """
        logger.info("Optimizing database...")

        self.conn.execute("ANALYZE")
        self.conn.execute("VACUUM")

        logger.info("✓ Optimization complete!")

    def select_query(self, query: str) -> DataFrame:
        """
        Executes a SELECT query and returns the result as a DataFrame.
        Args:
            query (str): The SELECT SQL query to execute.
        Returns:
            DataFrame: Resulting DataFrame from the query.
        """
        df: DataFrame = read_sql_query(query, self.conn)
        return df

    def close(self) -> None:
        """
        Closes the database connection.
        """
        try:
            if self.conn:
                self.conn.close()
                logger.info("Connection closed.")
        except Error as e:
            logger.error(f"Error closing connection: {e}")
            raise

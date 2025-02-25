import sqlite3
from sqlite3 import Error
from queue import Queue


class Tables:
    FLOW_MONIOTOR = "flow_monitor"
    RAIN_GAUGE = "rain_gauge"
    SURVEY_EVENT = "survey_event"
    SCHEMATIC_GRAPHICS_VIEW = "schematic_graphics_view"
    SUMMED_FLOW_MONITOR = "summed_flow_monitor"
    ICM_TRACE = "icm_trace"
    ICM_TRACE_LOCATION = "icm_trace_location"
    FSM_PROJECT = "fsm_project"
    FSM_SITE = "fsm_site"
    FSM_MONITOR = "fsm_monitor"
    FSM_INSTALL = "fsm_install"
    FSM_INTERIM = "fsm_interim"
    FSM_INTERIM_REVIEW = "fsm_interim_review"
    FSM_STORMEVENTS = "fsm_stormevent"
    FSM_INSPECTIONS = "fsm_inspection"
    FSM_INSTALLPICTURES = "fsm_installpicture"
    WQ_MONITOR = "wq_monitor"
    FB_VERSION = "fb_version"
    FSM_RAWDATA = "fsm_rawdata"


class DatabaseManager:
    """
    A class for managing database connections using a Singleton pattern.
    """

    _instance = None
    """
    Singleton instance of the DatabaseManager class.
    """

    def __new__(cls):
        """
        Create a new instance of DatabaseManager only if one does not already exist.

        Returns:
            DatabaseManager: An instance of the DatabaseManager class.
        """
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.database = None
            cls._instance.connection_pool = None
        return cls._instance

    def __init__(self):
        """
        Initialize the DatabaseManager instance.
        """
        if self.connection_pool is None:
            self.connection_pool = None
        if self.database is None:
            self.database = None

    def initialize(self, database, **kwargs):
        """
        Initialize the database connection pool.

        Args:
            database (str): The path to the SQLite database file.
            **kwargs: Additional keyword arguments to pass to the SQLiteConnectionPool constructor.
        """
        if self.connection_pool is None:
            self.database = database
            self.connection_pool = SQLiteConnectionPool(database, **kwargs)

    def get_connection(self):
        """
        Get a database connection from the connection pool.

        Returns:
            Connection: A database connection.

        Raises:
            Exception: If the connection pool is not initialized.
        """
        if self.connection_pool is None:
            raise Exception(
                "Connection pool not initialized. Call initialize() first.")
        return self.connection_pool.get_connection()

    def return_connection(self, conn):
        """
        Return a database connection to the connection pool.

        Args:
            conn (Connection): The database connection to return.

        Raises:
            Exception: If the connection pool is not initialized.
        """
        if self.connection_pool is None:
            raise Exception(
                "Connection pool not initialized. Call initialize() first.")
        self.connection_pool.return_connection(conn)

    def close_all_connections(self):
        """
        Close all database connections and reset the connection pool.

        Raises:
            Exception: If the connection pool is not initialized.
        """
        if self.connection_pool is not None:
            self.connection_pool.close_all_connections()
            self.connection_pool = None
            # DatabaseManager._instance = None

    def __del__(self):
        self.close_all_connections()
        # DatabaseManager._instance = None

    def is_connected(self):
        """
        Check if the database connection is initialized.

        Returns:
            bool: True if database is connected, False otherwise.
        """
        return self.connection_pool is not None


class SQLiteConnectionPool:
    def __init__(self, database, pool_size=5):
        self.database = database
        self.pool_size = pool_size
        self.connection_pool = Queue(maxsize=pool_size)
        for _ in range(pool_size):
            self._create_connection()

    def _create_connection(self):
        try:
            conn = sqlite3.connect(self.database)
            self.connection_pool.put(conn)
        except Error as e:
            print("Error creating SQLite connection:", e)

    def get_connection(self):
        if self.connection_pool.empty():
            self._create_connection()
        return self.connection_pool.get()

    def return_connection(self, conn):
        self.connection_pool.put(conn)

    def close_all_connections(self):
        while not self.connection_pool.empty():
            conn = self.connection_pool.get()
            conn.close()

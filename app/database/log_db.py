import sqlite3
from datetime import datetime

class SQLiteLogger:
    """Handles all logging to the SQLite database for audit trails."""

    def __init__(self, db_path):
        """
        Initializes the logger and creates the database and table if they don't exist.
        Args:
            db_path (str): The file path for the SQLite database.
        """
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        """Establishes and returns a connection to the database."""
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Creates the llm_api_logs table if it doesn't already exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_api_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                prompt TEXT,
                response TEXT,
                status TEXT NOT NULL,
                action_type TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def log_api_call(self, agent_name, prompt, response, status):
        """
        Logs a single call made to the Gemini API.
        Args:
            agent_name (str): The name of the agent making the call.
            prompt (str): The full prompt sent to the API.
            response (str): The full response received from the API.
            status (str): The outcome of the call ('success' or 'error').
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO llm_api_logs (timestamp, agent_name, prompt, response, status, action_type)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (datetime.utcnow().isoformat(), agent_name, str(prompt), str(response), status, "api_call")
        )
        conn.commit()
        conn.close()

    def log_manual_action(self, action_name, details):
        """
        Logs a manual user action, like deleting a node.
        Args:
            action_name (str): The name of the action (e.g., 'delete_node').
            details (str): A description of the action.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO llm_api_logs (timestamp, agent_name, prompt, response, status, action_type)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (datetime.utcnow().isoformat(), "Manual Action", details, "", "success", action_name)
        )
        conn.commit()
        conn.close()

    def get_all_logs(self):
        """

        Retrieves all log entries from the database.
        Returns:
            list: A list of dictionaries, where each dictionary is a log entry.
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM llm_api_logs ORDER BY timestamp DESC")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

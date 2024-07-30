import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd
from user_operations_analysis import (
    check_postgres_connection,
    get_dune_data,
    DUNE_QUERY_ID,
    DUNE_API_KEY,
    START_DATE,
)


class TestUserOperationsAnalysis(unittest.TestCase):
    @patch("airflow.hooks.base.BaseHook.get_connection")
    def test_check_postgres_connection(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_conn.conn_id = "postgres_default"
        mock_get_connection.return_value = mock_conn

        check_postgres_connection()
        mock_get_connection.assert_called_once_with("postgres_default")

    @patch("user_operations_analysis.DuneClient")
    @patch("airflow.providers.postgres.hooks.postgres.PostgresHook")
    def test_get_dune_data(self, mock_postgres_hook, mock_dune_client):
        mock_dune_instance = mock_dune_client.return_value
        mock_dune_instance.run_query_dataframe.return_value = pd.DataFrame(
            {
                "block_time": ["2024-07-30 16:27"],
                "block_number": [59994770],
                "contract_address": ["0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789"],
                "event_signature": [
                    "0x49628fd1471006c1482da88028e9ce4dbb080b815c9b0344d39e5a8e6ec1419f"
                ],
                "userOpHash": [
                    "0x08f952695424ca15aaff42a590fb4217e69e414925393d9a864de5f7056429f2"
                ],
                "sender": [
                    "0x0000000000000000000000005c7a9bf80924c9917e9c528be8568bc490219002"
                ],
                "paymaster": [
                    "0x0000000000000000000000004fd9098af9ddcb41da48a1d78f91f1398965addc"
                ],
                "transaction_hash": [
                    "0x083969a2e778dcf5e311aa85bd337a912b3bd9d8bd24dc1b7db5c778ec702c5f"
                ],
            }
        )

        mock_postgres_hook_instance = mock_postgres_hook.return_value
        mock_engine = mock_postgres_hook_instance.get_sqlalchemy_engine.return_value

        get_dune_data()

        mock_dune_instance.run_query_dataframe.assert_called_once()
        mock_postgres_hook_instance.get_sqlalchemy_engine.assert_called_once()
        mock_engine.connect.assert_called_once()


if __name__ == "__main__":
    unittest.main()

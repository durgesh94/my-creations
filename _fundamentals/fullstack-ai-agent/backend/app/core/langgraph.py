
import os

from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from langgraph.checkpoint.postgres.aio import (
    AsyncPostgresSaver,
)

load_dotenv()


def create_checkpoint_pool() -> AsyncConnectionPool:
    database_url = os.environ["LANGGRAPH_DATABASE_URL"]

    return AsyncConnectionPool(
        conninfo=database_url,
        min_size=1,
        max_size=5,
        open=False,
        kwargs={
            "autocommit": True,
            "row_factory": dict_row,
        },
    )


def create_checkpointer(
    pool: AsyncConnectionPool,
) -> AsyncPostgresSaver:
    return AsyncPostgresSaver(pool)

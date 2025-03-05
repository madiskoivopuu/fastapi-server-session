# Copyright (c) 2022 DevGuyAhnaf

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from datetime import datetime, timedelta, timezone
from uuid import UUID

from .base import BaseSessionInterface

import json

try:
    import aiomysql, pymysql
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "AsyncMysqlSessionInterface requires 'aiomysql' to be installed. Install it using 'pip install aiomysql'"
    )

_TABLE_CREATE_QUERY = """CREATE TABLE IF NOT EXISTS sessions (
	`session_id` binary(16) NOT NULL,
	`session_data` json NOT NULL,
	`expires_at_utc` datetime NOT NULL,
	PRIMARY KEY (`session_id`)
);
""" 

_SESSION_DELETE_SCHEDULE = """CREATE EVENT IF NOT EXISTS delete_expired_sessions
    ON SCHEDULE EVERY 4 HOUR
    DO
        DELETE FROM sessions WHERE expires_at_utc < UTC_TIMESTAMP() - INTERVAL 5 MINUTE
"""

class AsyncMysqlSessionInterface(BaseSessionInterface):
    """
    Interface for async MySQL client

    args:
        pool_ctx: aiomysql connection pool context manager
            You can get it by using aiomysql.create_pool(...)
    """
    def __init__(
        self,
        pool_ctx: aiomysql.utils._PoolContextManager,
    ):
        self._pool_ctx = pool_ctx
        self.pool = None
        self._initiated = False

    async def _init(self):
        if(self._initiated == True):
            return

        self.pool = await self._pool_ctx

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(_TABLE_CREATE_QUERY)
                await cursor.execute(_SESSION_DELETE_SCHEDULE)

                await conn.commit()

        self._initiated = True

    async def _set_session_data(self, session_id: str, data: dict, expiration_date: datetime | None):
        await self._init()

        session_data = json.dumps(data)
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if(expiration_date is not None):
                    expiration_date = expiration_date.astimezone(timezone.utc)

                q = """INSERT INTO sessions 
                                        (session_id, session_data, expires_at_utc) 
                                    VALUES 
                                        (UUID_TO_BIN(%s, 1), %s, %s) 
                                    ON DUPLICATE KEY UPDATE 
                                        session_data = %s""" # exp date is not None for a new session
                q_params = [session_id, session_data, expiration_date, session_data]

                await cursor.execute(q, q_params)
                await conn.commit()

    async def _get_session_data(self, session_id: str) -> dict:
        await self._init()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT session_data FROM sessions WHERE session_id = UUID_TO_BIN(%s, 1)", (session_id, ))
                data = await cursor.fetchone()
                if(data == None):
                    return None
                
                json_data = data[0]
                return json.loads(json_data)

    async def _delete_session(self, session_id: str):
        await self._init()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("DELETE FROM sessions WHERE session_id = UUID_TO_BIN(%s, 1)", (session_id, ))

    async def _get_expiration_date(self, session_id: str):
        await self._init()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT expires_at_utc FROM sessions WHERE session_id = UUID_TO_BIN(%s, 1)", (session_id, ))
                data = await cursor.fetchone()
                if(data == None):
                    return None
                
                return data[0].replace(tzinfo=timezone.utc)
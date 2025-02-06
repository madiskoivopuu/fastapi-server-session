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
    import aiomysql
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
""" # TODO: add schedule to delete expired sessions

class AsyncMysqlSessionInterface(BaseSessionInterface):
    """
    Interface for async MySQL client

    args:
        pool: aiomysql connection pool
    kwargs:
        table: name of the MySQL table where session info is stored
    optional:
    All Optional parameters are kwargs
        until_expires: timedelta object for ttl
    """
    def __init__(
        self,
        pool: aiomysql.Pool,
        until_expires: timedelta = timedelta(days=15)
    ):
        self.pool = pool
        self.expire = until_expires
        self._table_created = False

    async def init_tables(self):
        if(self._table_created == True):
            return

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(_TABLE_CREATE_QUERY)

                await conn.commit()

        self._table_created = True

    async def _set_session_data(self, session_id: str, data: dict, expiration_date: datetime):
        await self.init_tables()

        session_data = json.dumps(data)
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""INSERT INTO sessions 
                                        (session_id, session_data, expires_at_utc) 
                                     VALUES 
                                        (UUID_TO_BIN(%s, 1), %s, %s) 
                                     ON DUPLICATE KEY UPDATE 
                                        session_data = %s""", (session_id, session_data, expiration_date, session_data))
                await conn.commit()

    async def _get_session_data(self, session_id: str) -> dict:
        await self.init_tables()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT session_data FROM sessions WHERE session_id = UUID_TO_BIN(%s, 1)", (session_id, ))
                data = await cursor.fetchone()
                if(data == None):
                    return None
                
                json_data = data[0]
                return json.loads(json_data)

    async def _delete_session(self, session_id: str):
        await self.init_tables()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("DELETE FROM sessions WHERE session_id = UUID_TO_BIN(%s, 1)", (session_id, ))

    async def _get_expiration_date(self, session_id):
        await self.init_tables()

        return await super()._get_expiration_date(session_id)

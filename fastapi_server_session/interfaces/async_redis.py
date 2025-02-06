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

from .base import BaseSessionInterface
from datetime import datetime, timedelta, timezone

try:
    from redis import asyncio as aioredis
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "AsyncRedisSessionInterface requires 'redis' to be installed. Install it using 'pip install redis'"
    )

import json


class AsyncRedisSessionInterface(BaseSessionInterface):
    def __init__(
        self, 
        redis_client: aioredis.Redis,
    ):
        self.redis = redis_client

    async def _set_session_data(self, session_id: str, data: dict, expiration_date: datetime | None):
        sec_until_exp: int | None = None
        if(expiration_date != None):
            sec_until_exp = int((datetime.now(timezone.utc) - expiration_date).total_seconds())

        await self.redis.set(
            session_id, json.dumps(data), ex=sec_until_exp
        )

    async def _get_session_data(self, session_id: str) -> dict | None:
        try:
            return json.loads(await self.redis.get(session_id))
        except:
            return None

    async def _delete_session(self, session_id: str):
        await self.redis.delete(str(session_id))

    async def _get_expiration_date(self, session_id: str) -> datetime:
        ttl_left = await self.redis.ttl(session_id)
        if(ttl_left == -1):
            return 99999999999
        elif(ttl_left == -2):
            return None
        else:
            return datetime.now(timezone.utc) + timedelta(seconds=ttl_left)

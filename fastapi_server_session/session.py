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

from collections.abc import MutableMapping
from .interfaces.base import BaseSessionInterface
from fastapi import Response, Request
from typing import Optional
from dataclasses import dataclass

import uuid
from datetime import datetime, timezone, timedelta

@dataclass
class SessionSettings:
    create_or_renew: bool # Create new session if an existing one is expired or it doesn't exist

class SessionException(Exception):
    pass

class Session(MutableMapping):
    def __init__(
        self,
        response: Response,
        request: Request,
        interface: BaseSessionInterface,
        session_duration: timedelta,
        session_id: Optional[str] = None,

        session_settings: SessionSettings = SessionSettings(
            create_or_renew=False
        )
    ):
        self.response = response
        self.request = request
        self.session_id = session_id
        self.interface = interface
        self.session_duration = session_duration

        self._session_settings = session_settings
        self._expiration_date: datetime | None = None
        self._data = {}
        self.__entered = False

    def _validity_check(self):
        if(self.__entered == False):
            raise SessionException(message="Use `async with Session(...)` or FastAPI `session = Depends(...)` to correctly start the session")

    async def __aenter__(self):
        self.__entered = True

        self._expiration_date = await self.interface._get_expiration_date(self.session_id)
        self._data = await self.interface._get_session_data(self.session_id)
        if(datetime.now(timezone.utc) > self._expiration_date):
            if(not self._session_settings.create_or_renew):
                raise SessionException(message="Session has expired and automatic new session creation is disabled")

            await self.interface._delete_session(self.session_id)
            await self.initiate(
                uuid.uuid4(),
                {}
            )
        
        if(self._data == None):
            if(not self._session_settings.create_or_renew):
                raise SessionException(message="Session does not exist. Automatic new session creation is disabled")

            await self.initiate(
                uuid.uuid4(),
                {}
            )
        
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        self.__entered = False

        sess_exit_time = datetime.now(timezone.utc)
        if((self._expiration_date - sess_exit_time).total_seconds() < 0):
            await self.clear()
            raise SessionException(message="Session has expired")

        if(self._data != None): # session not deleted...
            await self.interface._set_session_data(self.session_id, self._data, self._expiration_date)

    async def initiate(self, session_id: str, data: dict) -> None:
        self.session_id = session_id

        expires_at_date = datetime.now(timezone.utc) + self.session_duration
        await self.interface._set_session_data(session_id, data, expires_at_date)
        self.response.set_cookie(
            "session", session_id, expires=self.session_duration.total_seconds(), httponly=True
        )  # Expires after 1 days

    async def clear(self) -> None:
        """Clears and deletes the session"""
        self._data = None
        await self.interface._delete_session(self.session_id)
        self.response.delete_cookie("session", httponly=True)

    def __setitem__(self, key, value) -> None:
        self._validity_check()

        self._data[key] = value
        pass

    def __getitem__(self, key) -> Optional[any]:
        self._validity_check()

        try:
            return self._data[key]
        except:
            return None

    def __delitem__(self, key) -> None:
        self._validity_check()

        try:
            del self._data[key]
        except (KeyError, TypeError):  # Session key did not exist or data is None
            return

    def __iter__(self):
        self._validity_check()
        
        return iter(self._data)

    def __len__(self) -> int:
        self._validity_check()

        return len(self._data)

    def __str__(self) -> str:
        self._validity_check()

        return str(self._data)

    def __repr__(self)-> str:
        return f"<{self.__class__.__name__} id={self.session_id}>"

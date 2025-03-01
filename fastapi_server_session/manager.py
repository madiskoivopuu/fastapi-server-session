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

from fastapi import Request, Response, HTTPException
from .interfaces.base import BaseSessionInterface
from .session import Session, SessionException
from datetime import timedelta
import uuid


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


class SessionManager:
    def __init__(self, interface: BaseSessionInterface, default_sess_duration: timedelta = timedelta(days=1)):
        self.interface = interface
        self.default_sess_duration = default_sess_duration

    async def get_session(self, request: Request, response: Response):
        """get_session yields an existing session object for a user
        
           If no session is found, None is yielded
        """
        session_id = str(request.cookies.get("session"))   
        if(not is_valid_uuid(session_id)):
            yield None
            return
        
        data = await self.interface._get_session_data(session_id)
        if(not data):
            yield None
            return

        try:
            session = Session(request=request,
                    response=response,
                    interface=self.interface,
                    session_id=session_id,
                    session_duration=self.default_sess_duration)
            async with session:
                yield session
        except SessionException:
            raise HTTPException(status_code=401, detail="Error fetching session")
        
    async def get_or_start_session(self, request: Request, response: Response):
        """get_session yields an session object
        
           If the session does not exist, a new one is created, with the data initially set to an empty dictionary
        """
        session_id = str(request.cookies.get("session"))        
        session = Session(request=request,
                    response=response,
                    interface=self.interface,
                    session_id=session_id,
                    session_duration=self.default_sess_duration)

        if(is_valid_uuid(session_id)):
            data = await self.interface._get_session_data(session_id)
            if(not data):
                await session.initiate(str(uuid.uuid4()), {})
        else:
            await session.initiate(str(uuid.uuid4()), {})
        
        try:
            async with session:
                yield session
        except SessionException:
            raise HTTPException(status_code=401, detail="Error fetching session")
        
    async def create_session(self, request: Request, response: Response) -> Session:
        """Creates a new session object with data set to an empty dictionary
        
           Returns a new session object, which overrides any existing session the user might have
        """
        session_id = str(uuid.uuid4())
        session = Session(request=request,
                    response=response,
                    interface=self.interface,
                    session_id=session_id,
                    session_duration=self.default_sess_duration)
        await session.initiate(session_id, {})
        return session



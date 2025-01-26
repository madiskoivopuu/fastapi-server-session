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

from abc import ABC, abstractmethod
from datetime import datetime


class BaseSessionInterface(ABC):
    """Base class for all session interfaces.
    All the abstract methods here will be implemented by interfaces
    """

    @abstractmethod
    async def _get_session_data(self, session_id: str) -> dict | None:
        """Returns session data for the specific request.

        If no session is available, returns None
        """

    @abstractmethod
    async def _set_session_data(self, session_id: str, data: dict, expires_at_date: datetime):
        """Stores session data  in a datastore."""

    @abstractmethod
    async def _delete_session(self, session_id: str):
        """Deletes the session including the data"""

    @abstractmethod
    async def _get_expiration_date(self, session_id: str) -> datetime | None:
        """Returns an UTC datetime denoting when the session will expire
        
        If no session is available, returns None
        """

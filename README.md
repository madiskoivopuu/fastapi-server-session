# FastAPI Server-sided Session

[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/Code%20Style-Black-black?style=flat-square)](https://github.com/psf/black)
[![pyvers](https://img.shields.io/badge/python-3.6+-blue?style=flat-square)]()

FastAPI Server Session is a dependency-based extension for FastAPI that adds support for server-sided session management.

At the moment, it supports using Redis and MongoDB as the session datastore. But in the future, it will support even more datastores including but not limited to SQL, etc.

## Quickstart


#### For async MySQL Backend

Note that using this backend requires the `UUID_TO_BIN` function to be present in MySQL.

```py
from fastapi_server_session import SessionManager, AsyncMysqlSessionInterface, Session
import pymongo
import aiomysql

session_manager = SessionManager(
    interface=AsyncMysqlSessionInterface(
        pool=await aiomysql.create_pool(host="127.0.0.1", port=3306, user="sessions", password="", db="sessions")
        table_name="session"
    )
)
```

#### For Redis & MongoDB Backend
These backends are currently not supported. While the implementations exist, they will no longer work after some tweaks that had to be done to get MySQL working.

If you wish to implement them yourself, fork the repo, create the implementations and then open a pull request.

#### Session usage

To connect each request with a session, use FastAPI's dependency injection as shown below:

```py
from fastapi import Depends, FastAPI, Request, Response

api = FastAPI()

@api.get("/auth")
async def get_session(request: Request, response: Response):
    session = session_manager.create_session(request, response)
    # to use the session right after creating it, you must use the *async with* clause
    # this must also be used, if you do not use FastAPI's dependency injection
    async with session:
        session["auth"] = "yes"
    return {"status": "new_session"} # Check the cookies that FastAPI returned in the response

@api.get("/set")
async def set_session(session: Session = Depends(session_manager.get_session)):
    if(session == None)
        return {"status": "unauthenticated"}

    session["key"] = "value"
    return {"status": "ok"}

@api.get("/get")
async def get_session(session: Session = Depends(session_manager.get_session)):
    return {"value": session["key"]} # or session.get("key")
```

Session manager also has a method called `get_or_start_session`, which will initiate a new session for a user, if it doesn't already exist. If you have a reason to automatically start a new session for each request, then prefer the use of this method.

## License

[MIT](https://choosealicense.com/licenses/mit/) License

Copyright (c) 2022 DevGuyAhnaf

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is

furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

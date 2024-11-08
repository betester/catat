
from collections.abc import Callable
from typing import Any
from fastapi import Request
from sqlmodel import Session
from starlette.responses import RedirectResponse

from auth import ExpiredException, verify_access_token
from data import LoginMethod
from global_state import app_state

async def user_authenticated(request: Request, call_next: Callable[[Request], Any]):
    auth_token = request.headers.get('Authorization')
    
    if not auth_token:
        return RedirectResponse(url='/auth/login')

    try:
        _, token, method = auth_token.split(" ")
        method = LoginMethod(method)
        db = app_state.db_engine

        with Session(db) as session:
            verify_access_token(token, method, session)
        
        call_next(request)

    except ExpiredException:
        return RedirectResponse(url="/auth/token")
        
    except Exception:
        return RedirectResponse(url="/auth/login")

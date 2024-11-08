
from fastapi import APIRouter, Response, status
from enum import StrEnum

from fastapi.responses import JSONResponse
from pydantic import BaseModel

from auth import get_google_oauth_certs, google_login, google_request_token, parse_token_id
from data import CatatUser, LoginMethod
from deps import AppConfigDep, DbDep


# TODO: add dependency for rerouting things when already token already exist
auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


class ErrorResponse(BaseModel):
    error_message: str


@auth_router.get("/login")
async def login(method: LoginMethod, app_config: AppConfigDep) -> Response:

    try:
        if method == LoginMethod.Google:
            return google_login(app_config.google_config)  
    except Exception as e:
        error_response = ErrorResponse(
            error_message = str(e)
        )
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=error_response) 

@auth_router.get("/google_callback")
async def google_redirect_login(code: str, scope: str, app_config: AppConfigDep, db: DbDep) -> Response:
    try:
        #TODO: store session token with refresh token as well 
        token_response = await google_request_token(code, scope, app_config.google_config)
        google_certs = await get_google_oauth_certs()
        client_id = app_config.google_config.client_id
        user_data = parse_token_id(token_response.id_token, client_id, google_certs.keys)

        new_user = CatatUser(
            email = user_data.email,
            full_name = user_data.name,
            profile_picture = user_data.picture
        ) 

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        #TODO: return the token and refresh token on the cookie instead
        return JSONResponse(content = new_user.model_dump_json(), status_code = status.HTTP_200_OK)

    except Exception as e:
        error_response = ErrorResponse(error_message = str(e))
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content = error_response)


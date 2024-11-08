
from fastapi import APIRouter, Depends, Response, status

from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime, timedelta

from auth import find_catat_user, get_google_oauth_certs, google_login, google_request_token, parse_token_id, store_catat_user, store_user_token
from data import CatatUser, CatatUserToken, LoginMethod
from deps import AppConfigDep, DbDep
from middleware import user_authenticated


auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(user_authenticated)]
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

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expiry_time: int
    method: LoginMethod

@auth_router.get("/google_callback")
async def google_redirect_login(code: str, scope: str, app_config: AppConfigDep, db: DbDep) -> Response:
    try:
        token_response = await google_request_token(code, scope, app_config.google_config)
        google_certs = await get_google_oauth_certs()
        client_id = app_config.google_config.client_id
        user_data = parse_token_id(token_response.id_token, client_id, google_certs.keys)

        existing_user = find_catat_user(user_data.email, db)

        new_user = CatatUser(
            email = user_data.email,
            full_name = user_data.name,
            profile_picture = user_data.picture
        ) 

        new_token = CatatUserToken(
            access_token=token_response.access_token,
            refresh_token=token_response.refresh_token,
            method= LoginMethod.Google,
            email=user_data.email,
            expiry_date= datetime.now() + timedelta(0, token_response.expires_in)
        )

        _ = store_user_token(new_token, db)
        if not existing_user: _ = store_catat_user(new_user, db)

        login_response = LoginResponse(
            access_token=token_response.access_token,
            refresh_token=token_response.refresh_token,
            expiry_time=token_response.expires_in,
            method=LoginMethod.Google
        )

        return JSONResponse(content = login_response.model_dump_json(), status_code = status.HTTP_200_OK)

    except Exception as e:
        error_response = ErrorResponse(error_message = str(e))
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content = error_response)


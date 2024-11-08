
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from httpx import AsyncClient
from jwt import decode, get_unverified_header
from jwt.algorithms import RSAAlgorithm
from sqlmodel import Session, select
from datetime import datetime

from conf import GoogleConfig
from data import CatatUser, CatatUserToken, LoginMethod

TOKEN_URL = "https://oauth2.googleapis.com/token"
CERT_URL = "https://www.googleapis.com/oauth2/v3/certs"

class GoogleTokenResponse(BaseModel):
    id_token: str
    access_token: str
    expires_in: int
    scope: str
    token_type: str

class GoogleTokenRequest(BaseModel):
    code: str
    client_id: str
    client_secret: str
    redirect_uri: str
    grant_type: str = "authorization_code"

class GoogleCert(BaseModel):
    n: str
    use: str
    e: str
    alg: str
    kid: str
    kty: str


class GoogleCertResponse(BaseModel):
    keys: list[GoogleCert]

class GoogleUserSession(BaseModel):
    email: str
    name: str
    picture: str

class ExpiredException(Exception):

    def __init__(self, expiry_date: datetime, current_time: datetime, error: object) -> None:
        super().__init__(error)
        self.expiry_date: datetime = expiry_date
        self.current_time: datetime = current_time

# TODO: cache this
async def get_google_oauth_certs() -> GoogleCertResponse:

    async with AsyncClient() as client:
        response = await client.get(CERT_URL)

        if response.is_error:
            iter = response.iter_text()
            message = " ".join(iter)
            raise Exception(message)

        response_content = response.content.decode(encoding='utf-8')
        return GoogleCertResponse.model_validate_json(response_content)

def google_login(google_config: GoogleConfig) -> RedirectResponse:

    client_id = google_config.client_id
    redirect_uri = google_config.redirect_uri
    scope = google_config.scope

    google_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"
    return RedirectResponse(url=google_url)

def parse_token_id(token_id: str, client_id: str, google_certs: list[GoogleCert]) -> GoogleUserSession:

    unverified_header = get_unverified_header(token_id)
    kid = unverified_header.get('kid')

    assert kid != None, "KID should be provided on the jwt header"

    for cert in google_certs:
        if cert.kid != kid:
            continue

        print(cert)

        rsa_key = RSAAlgorithm.from_jwk(cert.model_dump_json())
        
        #NOTE: ignore the warning it still compatible even the type aren't the same
        decoding_result: str = decode(jwt=token_id, key=rsa_key, algorithms=['RS256'], audience=client_id, strict=False)
        return GoogleUserSession.model_validate(decoding_result, strict=False)
    
    raise Exception("Could not parse the token id no matching kid")

async def google_request_token(authorization_code: str, scope: str, google_config: GoogleConfig):

    token_request = GoogleTokenRequest(
        code = authorization_code,
        client_id = google_config.client_id,
        client_secret = google_config.client_secret,
        redirect_uri = google_config.redirect_uri,
    )

    async with AsyncClient() as client:
        response = await client.post(
            url=TOKEN_URL,
            data= token_request.model_dump(),
            headers= { 'Content-Type': 'application/x-www-form-urlencoded' },
        )

        if response.is_error:
            iter = response.iter_text()
            message = " ".join(iter)
            raise Exception(message)
        response_content = response.content.decode(encoding='utf-8')
        return GoogleTokenResponse.model_validate_json(response_content)

def verify_access_token(access_token: str, method: LoginMethod, db: Session):

    statement = select(CatatUserToken).where(CatatUserToken.access_token == access_token and CatatUserToken.method == method)
    result = db.exec(statement).one()

    current_time = datetime.now()

    if result.expiry_date < current_time:
        raise ExpiredException(result.expiry_date, current_time, "Token expired")

from typing import cast, Annotated
from urllib.parse import quote
import secrets

from fastapi import HTTPException, status, Request, Depends
from kenar import Scope, OauthResourceType

from _types import UserID
from divar import divar_client
from config import config
import exception
from api_deps import get_repo
from repo import AuctionRepo


async def get_user_id_from_session(request: Request) -> UserID:
    user_id = request.session.get("user_id")
    if user_id is None:
        raise exception.InvalidSession("Invalid Session")
    return UserID(user_id)


async def get_user_id_from_session_no_error(
    request: Request, user_id: UserID | None = None
) -> UserID:
    if config.debug:
        return user_id or UserID("")
    user_id = request.session.get("user_id")
    if user_id is None:
        return UserID("")
    return UserID(user_id)


async def authorize_user(
    request: Request,
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
    user_id: Annotated[UserID, Depends(get_user_id_from_session_no_error)],
    code: str | None = None,
    state: str | None = None,
) -> list[UserID]:
    if config.debug:
        if user_id:
            request.session["user_id"] = user_id
            return [user_id]
        return [UserID("")]

    if user_id:
        return [user_id]

    if code is None:
        scope = Scope(resource_type=OauthResourceType.USER_PHONE.name)
        state = secrets.token_urlsafe(16)

        # TODO: only save predefined expected data from a schema
        await auction_repo.save_session_data(
            state=state, data=dict(request.query_params)
        )

        redirect_url = divar_client.oauth.get_oauth_redirect(
            scopes=[scope], state=state
        )
        headers = {"location": quote(str(redirect_url), safe=":/%#?=@[]!$&'()*+,;")}
        # FIXME: return proper response isntead of raising exeption?
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers=headers
        )

    access_token_data = divar_client.oauth.get_access_token(authorization_token=code)
    user_data = divar_client.finder.get_user(access_token_data.access_token)
    user_ids = [cast(UserID, phone) for phone in user_data.phone_numbers]
    if user_ids:
        # TODO: set exp time on session
        request.session["user_id"] = user_ids[0]
    return user_ids

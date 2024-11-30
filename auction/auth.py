from typing import cast
from urllib.parse import quote

from fastapi import HTTPException, status, Request
from kenar import GetUserResponse, Scope, OauthResourceType

from _types import UserID
from divar import divar_client
from config import config
import exception


async def authorize_user(
    request: Request,
    code: str | None = None,
    user_id: UserID | None = None,  # FIXME: delete user_id
) -> list[UserID]:
    if config.debug:
        if user_id:
            request.session["user_id"] = user_id
            return [user_id]
        return [UserID("")]

    if code is None:
        scope = Scope(resource_type=OauthResourceType.USER_PHONE.name)
        # TODO: create proper state
        redirect_url = divar_client.oauth.get_oauth_redirect(scopes=[scope], state="")
        headers = {"location": quote(str(redirect_url), safe=":/%#?=@[]!$&'()*+,;")}
        # FIXME: return proper response isntead of raising exeption?
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers=headers
        )
    user: GetUserResponse = divar_client.finder.get_user(access_token=code)
    user_ids = [cast(UserID, phone) for phone in user.phone_numbers]
    request.session["user_id"] = user_ids[0]
    return user_ids


async def get_user_id_from_session(request: Request) -> UserID | None:
    user_id = request.session.get("user_id")
    if user_id is None:
        raise exception.InvalidSession("Invalid Session")
    return UserID(user_id)

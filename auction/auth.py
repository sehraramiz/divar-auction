from typing import cast
from urllib.parse import quote, urlencode

from fastapi import HTTPException, status, Request
from kenar import Scope, OauthResourceType

from _types import UserID
from divar import divar_client
import exception
from security import encrypt_data, decrypt_data


async def get_user_id_from_session(request: Request) -> UserID:
    user_id = request.session.get("user_id")
    if user_id is None:
        raise exception.InvalidSession("Invalid Session")
    return UserID(user_id)


async def authorize_user_and_set_session(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    user_id: UserID | None = None,
) -> UserID:
    from config import config

    if config.debug and user_id is not None:
        request.session["user_id"] = user_id
        return user_id

    user_id = request.session.get("user_id")
    if user_id:
        return UserID(user_id)

    if code and state:
        state_data = decrypt_data(state)
        query_params = state_data.get("query_params", {})
        context = state_data.get("context", "home")
        access_token_data = divar_client.oauth.get_access_token(
            authorization_token=code
        )
        user_data = divar_client.finder.get_user(access_token_data.access_token)

        if not user_data.phone_numbers:
            raise exception.InvalidSession()

        user_ids = [cast(UserID, phone) for phone in user_data.phone_numbers]
        # TODO: set exp time on session
        request.session["user_id"] = user_ids[0]

        redirect_url = str(request.url_for(context)) + "?" + urlencode(query_params)
        # FIXME: return proper response isntead of raising exeption?
        headers = {"location": quote(str(redirect_url), safe=":/%#?=@[]!$&'()*+,;")}
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers=headers
        )

    scope = Scope(resource_type=OauthResourceType.USER_PHONE.name)

    # TODO: encrypt data into state
    context = "home"
    route = request.scope["endpoint"]
    if route:
        context = route.__name__
    data = {"context": context, "query_params": dict(request.query_params)}
    state = encrypt_data(data)

    redirect_url = divar_client.oauth.get_oauth_redirect(scopes=[scope], state=state)
    headers = {"location": quote(str(redirect_url), safe=":/%#?=@[]!$&'()*+,;")}
    # FIXME: return proper response isntead of raising exeption?
    raise HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers=headers)

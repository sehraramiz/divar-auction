from typing import cast, Annotated
from urllib.parse import urlencode

from fastapi.responses import RedirectResponse
from fastapi import status, Request, Depends
from kenar import Scope, OauthResourceType
from pydantic.networks import AnyHttpUrl

from _types import UserID
from divar import divar_client
import exception
from security import encrypt_data, decrypt_data
from api_deps import get_repo
from repo import AuctionRepo
from config import config


async def get_user_id_from_session(request: Request) -> UserID:
    user_id = request.session.get("user_id")
    if user_id is None:
        raise exception.InvalidSession("Invalid Session")
    return UserID(user_id)


async def redirect_oauth(
    request: Request,
    code: str,
    state: str,
) -> AnyHttpUrl:
    state_data = decrypt_data(state)
    query_params = state_data.get("query_params", {})
    query_params["state"] = state
    query_params["code"] = code
    context = state_data.get("context", "home")

    redirect_url = str(request.url_for(context)) + "?" + urlencode(query_params)
    return AnyHttpUrl(redirect_url)


async def authorize_user_and_set_session(
    request: Request,
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
    code: str | None = None,
    state: str | None = None,
    user_id: UserID | None = None,
) -> UserID:
    if config.debug and user_id is not None:
        request.session["user_id"] = user_id
        return user_id

    user_id = request.session.get("user_id")
    if user_id:
        return UserID(user_id)

    if code and state:
        state_data = decrypt_data(state)
        context = state_data.get("context", "home")
        access_token_data = divar_client.oauth.get_access_token(
            authorization_token=code
        )
        user_data = divar_client.finder.get_user(access_token_data.access_token)

        if not user_data.phone_numbers:
            raise exception.InvalidSession()

        user_ids = [cast(UserID, phone) for phone in user_data.phone_numbers]
        request.session["user_id"] = user_ids[0]

        await auction_repo.add_user_access_token(
            UserID(user_ids[0]),
            access_token_data=access_token_data.model_dump(mode="json"),
        )
        return user_ids[0]

    scope = Scope(resource_type=OauthResourceType.USER_PHONE.name)

    context = "home"
    route = request.scope["endpoint"]
    if route:
        context = route.__name__
    data = {"context": context, "query_params": dict(request.query_params)}
    state = encrypt_data(data)

    redirect_url = divar_client.oauth.get_oauth_redirect(scopes=[scope], state=state)
    RedirectResponse(url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    return UserID("")


async def user_get_posts_permission(
    request: Request,
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
    user_id: Annotated[UserID, Depends(authorize_user_and_set_session)],
    code: str | None = None,
    state: str | None = None,
) -> str:
    if config.debug:
        return ""

    access_token = await auction_repo.get_user_access_token_by_scope(
        user_id=user_id, scope=OauthResourceType.USER_POSTS_GET.value
    )
    if access_token:
        return access_token["access_token"]

    if code and state:
        state_data = decrypt_data(state)
        context = state_data.get("context", "home")
        access_token_data = divar_client.oauth.get_access_token(
            authorization_token=code
        )
        await auction_repo.add_user_access_token(
            UserID(user_id),
            access_token_data=access_token_data.model_dump(mode="json"),
        )
        return access_token_data.access_token

    scope = Scope(resource_type=OauthResourceType.USER_POSTS_GET.name)

    context = "home"
    route = request.scope["endpoint"]
    if route:
        context = route.__name__
    data = {"context": context, "query_params": dict(request.query_params)}
    state = encrypt_data(data)

    redirect_url = divar_client.oauth.get_oauth_redirect(scopes=[scope], state=state)
    RedirectResponse(url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    return ""

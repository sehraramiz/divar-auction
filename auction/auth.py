from typing import cast
from urllib.parse import quote

from fastapi import HTTPException, status

from kenar import GetUserResponse, Scope, OauthResourceType
from _types import UserID
from divar import divar_client
from config import config


async def authorize_user(
    code: str | None = None,
    user_id: UserID | None = None,  # FIXME: delete user_id
) -> list[UserID]:
    if config.debug:
        if user_id:
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
    return [cast(UserID, phone) for phone in user.phone_numbers]


if __name__ == "__main__":
    import asyncio
    import sys

    code = ""
    if len(sys.argv) > 1:
        code = sys.argv[1]
    user_ids = asyncio.run(authorize_user(code=code))
    print(user_ids)

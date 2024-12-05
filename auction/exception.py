from urllib.parse import quote

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import HTMLResponse, Response

from auction.i18n import gettext as _
from auction.pages.template import templates


class AuctionNotFound(HTTPException):
    def __init__(self, detail: str = _("Auction Not Found")):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BidNotFound(HTTPException):
    def __init__(self, detail: str = _("Bid Not Found")):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class PostNotFound(HTTPException):
    def __init__(self, detail: str = _("Post Not Found")):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class AuctionAlreadyStarted(HTTPException):
    def __init__(self, detail: str = _("Auction Already Started")):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class BidFromSellerNotAllowed(HTTPException):
    def __init__(self, detail: str = _("Seller Can't Bid")):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class BidTooLow(HTTPException):
    def __init__(self, detail: str = _("Bid can't be lower than the starting price")):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class InvalidSession(HTTPException):
    def __init__(self, detail: str = _("Invalid Session")):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class Forbidden(HTTPException):
    def __init__(self, detail: str = _("Forbidden")):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class OAuthRedirect(HTTPException):
    """This class is used to redirect user in a dependency function"""

    def __init__(self, redirect_url: str):
        headers = {"location": quote(str(redirect_url), safe=":/%#?=@[]!$&'()*+,;")}
        super().__init__(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers=headers
        )


async def handle_404(request: Request, exc: HTTPException) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name="404.html", status_code=exc.status_code
    )


async def handle_validation_error(
    request: Request, exc: RequestValidationError | ResponseValidationError
) -> HTMLResponse:
    status_code = status.HTTP_400_BAD_REQUEST
    if type(exc) is ResponseValidationError:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={"errors": exc.errors()},
        status_code=status_code,
    )


async def handle_error(request: Request, exc: HTTPException) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={"error_details": exc.detail},
        status_code=exc.status_code,
    )


async def ignore_oauth_redirect(request: Request, exc: OAuthRedirect) -> Response:
    return Response(headers=exc.headers, status_code=exc.status_code)


exception_handlers = {
    OAuthRedirect: ignore_oauth_redirect,
    status.HTTP_404_NOT_FOUND: handle_404,
    RequestValidationError: handle_validation_error,
    ResponseValidationError: handle_validation_error,
    HTTPException: handle_error,
}

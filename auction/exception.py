from urllib.parse import quote

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from auction.config import config


templates = Jinja2Templates(directory=config.templates_dir_path)


class AuctionNotFound(HTTPException):
    def __init__(self, detail: str = "Auction Not Found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class PostNotFound(HTTPException):
    def __init__(self, detail: str = "Post Not Found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class AuctionAlreadyStarted(HTTPException):
    def __init__(self, detail: str = "Auction Already Started"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class BidFromSellerNotAllowed(HTTPException):
    def __init__(self, detail: str = "Seller Can't Bid"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class BidTooLow(HTTPException):
    def __init__(self, detail: str = "Bid can't be lower than the starting price"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class InvalidSession(HTTPException):
    def __init__(self, detail: str = "Invalid Session"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class Forbidden(HTTPException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class OAuthRedirect(HTTPException):
    """This class is used to redirect user in a dependency function"""

    def __init__(self, redirect_url: str):
        headers = {"location": quote(str(redirect_url), safe=":/%#?=@[]!$&'()*+,;")}
        super().__init__(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers=headers
        )


async def handle_404(request: Request, exc: HTTPException) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="404.html")


async def handle_validation_error(
    request: Request, exc: RequestValidationError | ResponseValidationError
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name="error.html", context={"errors": exc.errors()}
    )


async def handle_response_validation_error(
    request: Request, exc: ResponseValidationError
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name="error.html", context={"errors": exc.errors()}
    )


async def handle_error(request: Request, exc: HTTPException) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name="error.html", context={"error_details": exc.detail}
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

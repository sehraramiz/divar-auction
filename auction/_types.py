from typing import Annotated, NewType
from uuid import UUID

from pydantic import AfterValidator, HttpUrl, NonNegativeInt, UrlConstraints

from auction.core.i18n import gettext as _


Rial = NewType("Rial", NonNegativeInt)
UserID = NewType("UserID", str)  # TODO: add phone number regex validation
PostToken = NewType("PostToken", str)
AuctionID = NewType("AuctionID", UUID)
BidderID = NewType("BidderID", UUID)
BidID = NewType("BidID", UUID)


def _only_divar_domain(url: HttpUrl) -> HttpUrl:
    if url.host != "divar.ir":
        raise ValueError(_("return url must be from divar.ir domain"))
    return url


DivarReturnUrl = Annotated[
    HttpUrl,
    UrlConstraints(allowed_schemes=["https"]),
    AfterValidator(_only_divar_domain),
]

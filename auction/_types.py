from typing import NewType
from uuid import UUID

from pydantic import NonNegativeInt


Rial = NewType("Rial", NonNegativeInt)
UserID = NewType("UserID", str)  # TODO: add phone number regex validation
PostToken = NewType("PostToken", str)
AuctionID = NewType("AuctionID", UUID)
BidderID = NewType("BidderID", UUID)
BidID = NewType("BidID", UUID)

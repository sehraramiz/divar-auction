from uuid import UUID
from typing import NewType

from pydantic import PositiveInt


Rial = NewType("Rial", PositiveInt)
UserID = NewType("UserID", str)  # TODO: add phone number regex validation
AdID = NewType("AdID", str)
AuctionID = NewType("AuctionID", UUID)
BidderID = NewType("BidderID", UUID)

from fastapi.exceptions import HTTPException
from fastapi import status


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

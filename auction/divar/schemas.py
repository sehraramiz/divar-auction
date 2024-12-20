from kenar import GetPostResponse


class PostItemResponse(GetPostResponse):
    first_published_at: str | None = None

    @classmethod
    def dummy(cls, post_token: str) -> "PostItemResponse":
        from kenar import PostExtState

        return cls(
            state=PostExtState.PUBLISHED.value,
            first_published_at=None,
            token=post_token,
            category="",
            city="",
            district="",
            data={},
        )

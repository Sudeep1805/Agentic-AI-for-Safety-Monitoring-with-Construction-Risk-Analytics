from starlette.responses import JSONResponse


class UploadBodyLimitMiddleware:
    """Bound multipart bodies before Starlette parses/spools them, including chunked requests."""

    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        try:
            too_large = int(headers.get(b"content-length", b"0")) > self.max_bytes
        except ValueError:
            return await JSONResponse({"detail": "Invalid Content-Length."}, 400)(scope, receive, send)
        body = bytearray()
        while not too_large:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            too_large = len(body) + len(chunk) > self.max_bytes
            if too_large:
                break
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        if too_large:
            return await JSONResponse({"detail": "Upload request exceeds the configured size limit."}, 413)(scope, receive, send)

        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)

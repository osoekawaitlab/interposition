# Reference Implementation: urllib Handler
#
# This example demonstrates how to integrate Interposition with Python's standard
# 'urllib.request' library by creating a custom BaseHandler.
# This is suitable for unit testing Python code without external dependencies.
#
# Usage:
#   python3 examples/http_urllib_adapter.py

"""Reference Implementation of a urllib Handler using Interposition.

This module provides a handler that intercepts urllib.request calls
and replays responses from an Interposition Broker.
"""

import logging
from http.client import HTTPResponse
from io import BytesIO
from urllib.error import URLError
from urllib.request import BaseHandler, Request, build_opener

from interposition import (
    Broker,
    Cassette,
    Interaction,
    InteractionRequest,
    ResponseChunk,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class MockSocket:
    """Mock socket object that provides a makefile method."""

    def __init__(self, data: bytes) -> None:
        """Initialize with data.

        Args:
            data: Raw HTTP response data.
        """
        self.data = data

    def makefile(self, _mode: str = "rb", *_args: object, **_kwargs: object) -> BytesIO:
        """Return a file-like object containing the response data."""
        return BytesIO(self.data)


class InterpositionHandler(BaseHandler):
    """A urllib BaseHandler that delegates to an Interposition Broker."""

    def __init__(self, broker: Broker) -> None:
        """Initialize the handler with a broker.

        Args:
            broker: The Interposition Broker to use for replay.
        """
        self.broker = broker

    def default_open(self, req: Request) -> HTTPResponse:
        """Intercept all requests and attempt replay.

        Note: In a standard urllib chain, 'default_open' is a catch-all.
        You might also implement protocol_request (http_request, https_request)
        for finer control, but default_open captures everything the opener handles.
        """
        return self._replay(req)

    def _replay(self, req: Request) -> HTTPResponse:
        # 1. Convert urllib.request.Request to Interposition InteractionRequest
        # Handle method
        method = req.get_method() or "GET"

        # Handle URL
        url = req.full_url

        # Handle Headers
        # For simplicity in this example, we ignore headers in the matching logic.
        # urllib adds default headers (User-Agent, etc.) which would cause
        # strict matching to fail unless we recorded them exactly.
        headers = ()

        # Handle Body
        # urllib.request.Request.data can be bytes or an iterable of bytes
        raw_body = req.data
        body = b""
        if isinstance(raw_body, bytes):
            body = raw_body
        elif raw_body is not None:
            # Fallback for other potential types (iterables, etc.)
            try:
                body = b"".join(raw_body)  # type: ignore[arg-type]
            except (TypeError, AttributeError):
                body = bytes(raw_body)  # type: ignore[arg-type]

        inter_req = InteractionRequest(
            protocol="http",
            action=method,
            target=url,
            headers=headers,
            body=body,
        )

        try:
            # 2. Replay via Broker
            # This will raise InteractionNotFoundError if no match is found.
            response_generator = self.broker.replay(inter_req)
        except Exception as e:
            # Wrap internal errors as URLError to play nice with urllib
            logger.warning("Interposition failed to find match for %s: %s", url, e)
            raise URLError(reason=str(e)) from e

        # 3. Convert Interposition response stream back to HTTPResponse
        # Consuming the generator to build the full body
        full_content = b""
        for chunk in response_generator:
            full_content += chunk.data

        # Construct a raw HTTP response (Status Line + Headers + Body)
        # This allows resp.begin() to parse it naturally.
        # In a real adapter, you'd reconstruct this from stored metadata.
        status_line = b"HTTP/1.1 200 OK\r\n"
        headers_raw = b"Content-Type: application/json\r\n"
        content_length = f"Content-Length: {len(full_content)}\r\n".encode()
        raw_response = (
            status_line + headers_raw + content_length + b"\r\n" + full_content
        )

        # Construct a fake socket/file-like object for HTTPResponse
        sock = MockSocket(raw_response)

        # Create HTTPResponse
        # HTTPResponse expects a real socket object. We use type: ignore to
        # provide our MockSocket which implements the required makefile().
        resp = HTTPResponse(sock, method=method, url=url)  # type: ignore[arg-type]
        resp.begin()

        return resp


# --- Usage Example ---


def run_example() -> None:
    """Run a demonstration of the InterpositionHandler."""
    # 1. Setup Data
    req_data = InteractionRequest(
        protocol="http",
        action="GET",
        target="https://api.example.com/users/1",
        headers=(),
        body=b"",
    )

    resp_data = (ResponseChunk(data=b'{"id": 1, "name": "Alice"}', sequence=0),)

    interaction = Interaction(
        request=req_data,
        fingerprint=req_data.fingerprint(),
        response_chunks=resp_data,
    )

    cassette = Cassette(interactions=(interaction,))
    broker = Broker(cassette)

    # 2. Configure urllib to use our Handler
    handler = InterpositionHandler(broker)
    opener = build_opener(handler)

    # 3. Make a request
    logger.info("Sending request to https://api.example.com/users/1 ...")
    try:
        response = opener.open("https://api.example.com/users/1")

        # Use type: ignore to access HTTPResponse attributes which might be hidden
        # by the return type of opener.open() (which is client.HTTPResponse | Any
        # or similar depending on the environment).
        logger.info("Status: %s", response.code)
        body = response.read().decode("utf-8")
        logger.info("Body: %s", body)

        # Verify
        if body != '{"id": 1, "name": "Alice"}':
            msg = "Response did not match expected data"
            raise RuntimeError(msg)
        logger.info("Success!")

    except URLError:
        logger.exception("Request failed")


if __name__ == "__main__":
    run_example()

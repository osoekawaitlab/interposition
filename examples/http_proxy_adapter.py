# Reference Implementation: Simple HTTP Proxy Server
#
# This example demonstrates how to expose Interposition as an HTTP Proxy.
# This is suitable for E2E testing (e.g., configuring an app to use this proxy)
# or when the client is not written in Python.
#
# Usage:
#   1. Run this script. It starts a server on localhost:8080.
#   2. Configure your client (e.g., curl) to use this proxy.
#      export http_proxy=http://localhost:8080
#      curl http://example.com/api/data

"""Reference Implementation of a simple HTTP Proxy Server using Interposition.

This module provides a basic HTTP proxy that intercepts requests and replays
responses from an Interposition Broker.
"""

import http.server
import logging
import socketserver

from interposition import (
    Broker,
    Cassette,
    Interaction,
    InteractionNotFoundError,
    InteractionRequest,
    ResponseChunk,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

PORT = 8080


# --- Setup Shared Broker (Mock Data) ---
def create_mock_broker() -> Broker:
    """Create a mock broker with pre-defined interactions."""
    req_data = InteractionRequest(
        protocol="http",
        action="GET",
        target="http://example.com/api/data",
        headers=(),
        body=b"",
    )

    resp_data = (
        ResponseChunk(data=b'{"status": "ok", "source": "proxy"}', sequence=0),
    )

    interaction = Interaction(
        request=req_data,
        fingerprint=req_data.fingerprint(),
        response_chunks=resp_data,
    )

    cassette = Cassette(interactions=(interaction,))
    return Broker(cassette)


GLOBAL_BROKER = create_mock_broker()


class InterpositionProxyHandler(http.server.BaseHTTPRequestHandler):
    """HTTP Request Handler that acts as a proxy, delegating to Interposition.

    Intercepts HTTP methods and attempts to replay them from the global broker.
    """

    def do_GET(self) -> None:
        """Handle GET requests."""
        self.handle_request("GET")

    def do_POST(self) -> None:
        """Handle POST requests."""
        self.handle_request("POST")

    def do_PUT(self) -> None:
        """Handle PUT requests."""
        self.handle_request("PUT")

    def do_DELETE(self) -> None:
        """Handle DELETE requests."""
        self.handle_request("DELETE")

    def handle_request(self, method: str) -> None:
        """Common request handler.

        Args:
            method: The HTTP method (GET, POST, etc.)
        """
        # 1. Capture Request
        length_header = self.headers.get("content-length", 0)
        length = int(length_header)
        body = self.rfile.read(length) if length > 0 else b""

        # In a real proxy, you'd want to capture headers too.
        # For simplicity, we ignore incoming headers in matching.

        inter_req = InteractionRequest(
            protocol="http",
            action=method,
            target=self.path,  # In proxy mode, path is often the full URL
            headers=(),
            body=body,
        )

        try:
            # 2. Replay
            logger.info("[Proxy] Intercepted: %s %s", method, self.path)
            response_gen = GLOBAL_BROKER.replay(inter_req)

            # 3. Send Response
            # Again, assuming simple 200 OK and body.
            # Real impl would store status/headers in chunks.
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            for chunk in response_gen:
                self.wfile.write(chunk.data)

        except InteractionNotFoundError:
            logger.warning("[Proxy] Not Found: %s %s", method, self.path)
            self.send_error(404, "Interaction not recorded in cassette")
        except Exception as e:
            # We must catch all exceptions here to send a 500 response to the client
            logger.exception("[Proxy] Error processing request")
            self.send_error(500, str(e))


class ReuseAddrTCPServer(socketserver.TCPServer):
    """TCPServer with allow_reuse_address enabled."""

    allow_reuse_address = True


def run_server() -> None:
    """Start the HTTP proxy server."""
    with ReuseAddrTCPServer(("", PORT), InterpositionProxyHandler) as httpd:
        logger.info("Serving Interposition Proxy at http://localhost:%s", PORT)
        logger.info("Try: curl -x http://localhost:8080 http://example.com/api/data")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()


if __name__ == "__main__":
    run_server()

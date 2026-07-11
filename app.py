#!/usr/bin/env python3
"""
Small local login website used as an OWASP ZAP Baseline target.

This application is only for CI/CD validation. It does not use a real
database or production authentication.
"""

from __future__ import annotations

import argparse
import html
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs


SITE_NAME = 'dome1'
SUBTITLE = 'A compact account portal for passive security-scan validation.'
ENABLE_STATUS_API = False


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__TITLE__</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      font-family: Arial, Helvetica, sans-serif;
      background: #f2f5f9;
      color: #1f2937;
    }
    main {
      width: min(92vw, 620px);
      padding: 30px;
      background: white;
      border: 1px solid #d7dee8;
      border-radius: 14px;
      box-shadow: 0 12px 30px rgba(31, 41, 55, 0.08);
    }
    nav { margin-bottom: 24px; }
    nav a { margin-right: 14px; }
    label { display: block; margin-top: 14px; font-weight: 600; }
    input, button {
      width: 100%;
      padding: 11px;
      margin-top: 6px;
      border: 1px solid #bac5d3;
      border-radius: 7px;
    }
    button {
      margin-top: 18px;
      cursor: pointer;
      font-weight: 700;
    }
    code {
      padding: 2px 5px;
      border-radius: 4px;
      background: #eef2f7;
    }
  </style>
</head>
<body>
  <main>
    <nav>
      <a href="/">Home</a>
      <a href="/login">Login</a>
      <a href="/about">About</a>
      __STATUS_LINK__
    </nav>
    __BODY__
  </main>
</body>
</html>
"""


def render_page(title: str, body: str) -> bytes:
    status_link = (
        '<a href="/api/status">API status</a>'
        if ENABLE_STATUS_API
        else ""
    )
    document = (
        HTML_TEMPLATE
        .replace("__TITLE__", html.escape(title))
        .replace("__STATUS_LINK__", status_link)
        .replace("__BODY__", body)
    )
    return document.encode("utf-8")


class ApplicationHandler(BaseHTTPRequestHandler):
    server_version = "DemoWeb/1.0"

    def _send_headers(
        self,
        status: HTTPStatus = HTTPStatus.OK,
        content_type: str = "text/html; charset=utf-8",
        content_length: int | None = None,
        *,
        set_cookie: bool = False,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "public, max-age=60")

        # Deliberately simple local-demo cookie.
        if set_cookie:
            self.send_header(
                "Set-Cookie",
                f"demo_session={SITE_NAME}; Path=/",
            )

        if content_length is not None:
            self.send_header("Content-Length", str(content_length))

        self.end_headers()

    def _write_html(
        self,
        title: str,
        body: str,
        status: HTTPStatus = HTTPStatus.OK,
        *,
        set_cookie: bool = False,
        head_only: bool = False,
    ) -> None:
        payload = render_page(title, body)
        self._send_headers(
            status,
            content_length=len(payload),
            set_cookie=set_cookie,
        )
        if not head_only:
            self.wfile.write(payload)

    def _serve_get(self, *, head_only: bool = False) -> None:
        path = self.path.split("?", 1)[0]

        if path == "/":
            self._write_html(
                f"{SITE_NAME} Home",
                f"""
                <h1>{html.escape(SITE_NAME)}</h1>
                <p>{html.escape(SUBTITLE)}</p>
                <p>This application is started by Docker Compose before
                the OWASP ZAP Baseline scan.</p>
                <p><a href="/login">Open the login page</a></p>
                """,
                head_only=head_only,
            )
            return

        if path == "/login":
            self._write_html(
                f"{SITE_NAME} Login",
                """
                <h1>Sign in</h1>
                <form method="post" action="/login">
                  <label for="username">Username</label>
                  <input id="username" name="username"
                         autocomplete="username" required>

                  <label for="password">Password</label>
                  <input id="password" name="password" type="password"
                         autocomplete="current-password" required>

                  <button type="submit">Login</button>
                </form>
                <p>Demo account: <code>demo / demo123</code></p>
                """,
                set_cookie=True,
                head_only=head_only,
            )
            return

        if path == "/about":
            self._write_html(
                f"About {SITE_NAME}",
                f"""
                <h1>About</h1>
                <p>{html.escape(SITE_NAME)} is a small local
                application used to verify startup, passive scanning,
                report generation, and dashboard ingestion.</p>
                """,
                head_only=head_only,
            )
            return

        if path == "/dashboard":
            self._write_html(
                f"{SITE_NAME} Dashboard",
                """
                <h1>Demo dashboard</h1>
                <p>The demonstration login was accepted.</p>
                <p><a href="/login">Return to login</a></p>
                """,
                head_only=head_only,
            )
            return

        if path == "/health":
            payload = b'{"status":"ok"}'
            self._send_headers(
                HTTPStatus.OK,
                "application/json; charset=utf-8",
                len(payload),
            )
            if not head_only:
                self.wfile.write(payload)
            return

        if ENABLE_STATUS_API and path == "/api/status":
            payload = (
                f'{"service":"{SITE_NAME}","status":"online"}'
            ).encode("utf-8")
            self._send_headers(
                HTTPStatus.OK,
                "application/json; charset=utf-8",
                len(payload),
            )
            if not head_only:
                self.wfile.write(payload)
            return

        self._write_html(
            "Not found",
            "<h1>404</h1><p>The requested page was not found.</p>",
            HTTPStatus.NOT_FOUND,
            head_only=head_only,
        )

    def do_GET(self) -> None:
        self._serve_get(head_only=False)

    def do_HEAD(self) -> None:
        self._serve_get(head_only=True)

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        if path != "/login":
            self._write_html(
                "Not found",
                "<h1>404</h1>",
                HTTPStatus.NOT_FOUND,
            )
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0

        raw_body = self.rfile.read(length).decode(
            "utf-8",
            errors="replace",
        )
        form = parse_qs(raw_body)

        username = form.get("username", [""])[0]
        password = form.get("password", [""])[0]

        if username == "demo" and password == "demo123":
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/dashboard")
            self.send_header(
                "Set-Cookie",
                f"authenticated={SITE_NAME}; Path=/",
            )
            self.end_headers()
            return

        self._write_html(
            "Login failed",
            """
            <h1>Login failed</h1>
            <p>The demonstration credentials were not accepted.</p>
            <p><a href="/login">Try again</a></p>
            """,
            HTTPStatus.UNAUTHORIZED,
        )

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.client_address[0]} - {fmt % args}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = ThreadingHTTPServer(
        ("0.0.0.0", args.port),
        ApplicationHandler,
    )
    print(f"{SITE_NAME} listening on http://0.0.0.0:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

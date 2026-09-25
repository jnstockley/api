"""
email_sender.py

A small, secure, dependency-free utility for sending email through a local
(or remote) SMTP server using Python's standard library.

Design goals:
- Secure by default (TLS/STARTTLS, no plaintext credentials in logs)
- Modern Python (type hints, dataclasses, context manager, pathlib)
- Performant for simple use (single persistent connection per batch via
  the context manager, so you don't reconnect for every message)

Templating: HTML/text bodies can be rendered from Jinja2 templates stored
on disk via TemplateRenderer + EmailSender.send_templated(). Requires the
'jinja2' package: pip install jinja2
"""

from __future__ import annotations

import html as html_lib
import logging
import mimetypes
import re
import smtplib
import ssl
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Self

import jinja2

logger = logging.getLogger(__name__)


@dataclass
class SMTPConfig:
    host: str = "localhost"
    port: int = 587
    username: str | None = None
    password: str | None = None
    use_ssl: bool = False  # True -> SMTPS (implicit TLS, usually port 465)
    use_starttls: bool = True  # True -> upgrade plaintext connection (usually port 587)
    timeout: float = 10.0
    # Set to False only for local/dev servers with self-signed certs.
    verify_tls: bool = True
    # Refuse to negotiate anything older than TLS 1.2 (TLS 1.3 will be used
    # automatically whenever both sides support it, since it's preferred by
    # the default context's own ordering).
    minimum_tls_version: ssl.TLSVersion = ssl.TLSVersion.TLSv1_2


class EmailSendError(RuntimeError):
    """Raised when a message could not be delivered."""


_TAG_RE = re.compile(r"<[^>]+>")


def _html_to_text(html_body: str) -> str:
    """
    Best-effort plain-text fallback derived from an HTML body, for callers
    who only supply an HTML template. Not a full HTML renderer -- good
    enough for a fallback that non-HTML mail clients will show, not a
    substitute for an intentionally written text template.
    """
    text = re.sub(r"(?is)<(script|style)\b.*?</\1>", "", html_body)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = _TAG_RE.sub("", text)
    text = html_lib.unescape(text)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line) or " "


class TemplateRenderer:
    """
    Renders email bodies from Jinja2 templates stored in a directory.

    Expected layout, e.g.:
        templates/
            welcome.html    # HTML body -- autoescaped
            welcome.txt     # optional plain-text counterpart -- not autoescaped

    HTML autoescaping is always on for .html/.htm templates, so values in
    `context` (a user's name, a comment, anything not written by you) can't
    inject markup or script into the rendered email. Undefined variables
    raise instead of silently rendering as empty strings, so a typo'd or
    missing field is caught at render time rather than mailed out blank.
    """

    def __init__(self, templates_dir: str | Path, strict: bool = True):
        self.templates_dir = Path(templates_dir)
        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)),
            autoescape=jinja2.select_autoescape(enabled_extensions=("html", "htm")),
            undefined=jinja2.StrictUndefined if strict else jinja2.Undefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self._env.get_template(template_name)
        except jinja2.TemplateNotFound as exc:
            raise FileNotFoundError(
                f"Template {template_name!r} not found in {self.templates_dir}"
            ) from exc
        try:
            return template.render(**context)
        except jinja2.UndefinedError as exc:
            raise ValueError(
                f"Missing field rendering {template_name!r}: {exc}"
            ) from exc


class EmailSender:
    """
    Secure SMTP email sender with connection reuse.

    Usage:
        config = SMTPConfig(host="localhost", port=587, username="me@example.com",
                             password="app-password")

        with EmailSender(config) as sender:
            sender.send(
                sender_addr="me@example.com",
                to=["you@example.com"],
                subject="Hello",
                body="Plain text body",
                html_body="<p>Optional HTML body</p>",
                attachments=["report.pdf"],
            )
    """

    def __init__(self, config: SMTPConfig):
        self.config = config
        self._connection: smtplib.SMTP | None = None

    # -- connection lifecycle -------------------------------------------------

    def connect(self) -> None:
        if self._connection is not None:
            return

        if (
            not self.config.use_ssl
            and not self.config.use_starttls
            and self.config.password
        ):
            raise ValueError(
                "Refusing to send credentials over an unencrypted connection: "
                "set use_ssl=True or use_starttls=True, or remove the password "
                "if you really intend to connect in plaintext."
            )

        context = ssl.create_default_context()
        context.minimum_version = self.config.minimum_tls_version
        if not self.config.verify_tls:
            # Only intended for trusted local/dev SMTP servers.
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            logger.warning(
                "TLS certificate verification is disabled for %s", self.config.host
            )

        if self.config.use_ssl:
            conn: smtplib.SMTP = smtplib.SMTP_SSL(
                self.config.host,
                self.config.port,
                timeout=self.config.timeout,
                context=context,
            )
        else:
            conn = smtplib.SMTP(
                self.config.host, self.config.port, timeout=self.config.timeout
            )
            conn.ehlo()
            if self.config.use_starttls:
                conn.starttls(context=context)
                conn.ehlo()

        if self.config.username and self.config.password:
            conn.login(self.config.username, self.config.password)

        self._connection = conn
        logger.info(
            "Connected to SMTP server %s:%s", self.config.host, self.config.port
        )

    def close(self) -> None:
        if self._connection is not None:
            try:
                self._connection.quit()
            except smtplib.SMTPException, OSError:
                self._connection.close()
            finally:
                self._connection = None

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # -- message construction / sending ----------------------------------------

    @staticmethod
    def _build_message(
        sender_addr: str,
        to: Sequence[str],
        subject: str,
        body: str,
        html_body: str | None = None,
        cc: Sequence[str] | None = None,
        bcc: Sequence[str] | None = None,
        reply_to: str | None = None,
        attachments: Iterable[str | Path] | None = None,
    ) -> tuple[EmailMessage, list[str]]:
        msg = EmailMessage()
        msg["From"] = sender_addr
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = ", ".join(cc)
        if reply_to:
            msg["Reply-To"] = reply_to

        msg.set_content(body)
        if html_body:
            msg.add_alternative(html_body, subtype="html")

        for path in attachments or []:
            path = Path(path)
            data = path.read_bytes()
            ctype, _ = mimetypes.guess_type(path.name)
            maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
            msg.add_attachment(
                data, maintype=maintype, subtype=subtype, filename=path.name
            )

        all_recipients = list(to) + list(cc or []) + list(bcc or [])
        return msg, all_recipients

    def send(
        self,
        sender_addr: str,
        to: Sequence[str],
        subject: str,
        body: str,
        html_body: str | None = None,
        cc: Sequence[str] | None = None,
        bcc: Sequence[str] | None = None,
        reply_to: str | None = None,
        attachments: Iterable[str | Path] | None = None,
    ) -> None:
        """Send a single email. Opens a connection automatically if not already open."""
        opened_here = False
        if self._connection is None:
            self.connect()
            opened_here = True

        msg, recipients = self._build_message(
            sender_addr, to, subject, body, html_body, cc, bcc, reply_to, attachments
        )

        try:
            assert self._connection is not None
            self._connection.send_message(
                msg, from_addr=sender_addr, to_addrs=recipients
            )
            logger.info("Sent email to %s recipients", len(recipients))
        except smtplib.SMTPException as exc:
            raise EmailSendError(f"Failed to send email: {exc}") from exc
        finally:
            if opened_here:
                self.close()

    def send_templated(
        self,
        renderer: TemplateRenderer,
        sender_addr: str,
        to: Sequence[str],
        subject: str,
        template: str,
        context: dict[str, Any],
        text_template: str | None = None,
        cc: Sequence[str] | None = None,
        bcc: Sequence[str] | None = None,
        reply_to: str | None = None,
        attachments: Iterable[str | Path] | None = None,
    ) -> None:
        """
        Render `template` (an HTML file in renderer.templates_dir) with
        `context` and send it.

        If `text_template` is given, that file is rendered too and used as
        the plain-text part (recommended -- write copy for text clients
        deliberately rather than relying on auto-stripped HTML). Otherwise
        a plain-text fallback is derived automatically from the rendered
        HTML.
        """
        html_body = renderer.render(template, context)
        body = (
            renderer.render(text_template, context)
            if text_template
            else _html_to_text(html_body)
        )

        self.send(
            sender_addr=sender_addr,
            to=to,
            subject=subject,
            body=body,
            html_body=html_body,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
            attachments=attachments,
        )

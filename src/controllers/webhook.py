import os

from fastapi import APIRouter, HTTPException, Security
from nctalk import TalkMessenger
from pydantic import BaseModel, Field

from util.auth import get_token_header
from util.logging import logger
from util.mail import EmailSender, SMTPConfig, TemplateRenderer

router = APIRouter(prefix="/webhook", dependencies=[Security(get_token_header)])


class NextcloudTalkWebhook(BaseModel):
    header: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=32000)


class PveUpsWebhook(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=32000)
    severity: str = Field(..., min_length=1, max_length=32000)
    severity_upper: str = Field(..., min_length=1, max_length=32000)
    facts: str = Field(..., min_length=1, max_length=32000)
    timestamp: str = Field(..., min_length=1, max_length=32000)
    version: str = Field(..., min_length=1, max_length=32000)
    to: str = Field(..., min_length=1, max_length=32000)


@router.post("/databasus")
async def databasus(webhook: NextcloudTalkWebhook):
    if webhook.header.strip() == "":
        raise HTTPException(status_code=422, detail="header cannot be empty")
    if webhook.message.strip() == "":
        raise HTTPException(status_code=422, detail="message cannot be empty")

    endpoint_url = os.environ.get("NEXTCLOUD_URL", "").strip()
    token = os.environ.get("NEXTCLOUD_TALK_TOKEN", "").strip()
    secret = os.environ.get("NEXTCLOUD_TALK_SECRET", "").strip()

    if not endpoint_url or not token or not secret:
        raise HTTPException(status_code=500, detail="Nextcloud Talk is not configured")
    if not endpoint_url.startswith("https://"):
        raise HTTPException(status_code=500, detail="NEXTCLOUD_URL must use https://")

    messenger = TalkMessenger(endpoint_url=endpoint_url, token=token, secret=secret)

    message = f"**{webhook.header}**\n{webhook.message}"

    if not messenger.send(message):
        logger.error("Failed to send message to Nextcloud Talk")
        raise HTTPException(
            status_code=502, detail="Failed to send message to Nextcloud Talk"
        )

    return {"status": "sent"}


@router.post("/pve-ups")
async def pve_ups(webhook: PveUpsWebhook):
    if not os.environ.get("SMTP_HOST") or not os.environ.get("SMTP_PORT"):
        raise HTTPException(status_code=500, detail="SMTP is not configured")
    if not os.environ.get("SMTP_USERNAME") or not os.environ.get("SMTP_PASSWORD"):
        raise HTTPException(
            status_code=500, detail="SMTP credentials are not configured"
        )

    if webhook.body.strip() == "":
        raise HTTPException(status_code=422, detail="body cannot be empty")
    if webhook.facts.strip() == "":
        raise HTTPException(status_code=422, detail="facts cannot be empty")
    if webhook.timestamp.strip() == "":
        raise HTTPException(status_code=422, detail="timestamp cannot be empty")
    if webhook.subject.strip() == "":
        raise HTTPException(status_code=422, detail="subject cannot be empty")
    if webhook.to.strip() == "":
        raise HTTPException(status_code=422, detail="to cannot be empty")
    if webhook.severity.strip() == "":
        raise HTTPException(status_code=422, detail="severity cannot be empty")
    if webhook.version.strip() == "":
        raise HTTPException(status_code=422, detail="version cannot be empty")
    if webhook.severity_upper.strip() == "":
        raise HTTPException(status_code=422, detail="severity_upper cannot be empty")

    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "0"))
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")

    smtp_config = SMTPConfig(host=host, port=port, username=username, password=password)

    with EmailSender(smtp_config) as sender:
        renderer = TemplateRenderer(templates_dir="templates")
        sender.send_templated(
            renderer=renderer,
            sender_addr="PVE UPS <no-reply@jstockley.com>",
            template="pve_ups_email.html",
            subject=webhook.subject,
            to=webhook.to,
            context={
                "body": webhook.body,
                "subject": webhook.subject,
                "facts": webhook.facts,
                "timestamp": webhook.timestamp,
                "severity": webhook.severity,
                "severity_upper": webhook.severity.upper(),
                "version": webhook.version,
            },
        )

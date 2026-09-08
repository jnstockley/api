import os

from fastapi import APIRouter, HTTPException, Security
from nctalk import TalkMessenger
from pydantic import BaseModel, Field

from util.auth import get_token_header
from util.logging import logger

router = APIRouter(prefix="/webhook", dependencies=[Security(get_token_header)])


class NextcloudTalkWebhook(BaseModel):
    header: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=32000)


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

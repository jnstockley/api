import datetime
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Security
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import engine
from models import IpAddress
from util.auth import get_token_header

router = APIRouter(prefix="/ip", dependencies=[Security(get_token_header)])

ipv4_pattern = re.compile(
    r"^([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(?<!172\.(16|17|18|19|20|21|22|23|24|25|26"
    r"|27|28|29|30|31))(?<!127)(?<!^10)(?<!^0)\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])"
    r"(?<!192\.168)(?<!172\.(16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31))\.([0-9]|[1-9][0-9]"
    r"|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
)

ipv6_pattern = re.compile(
    r"(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,"
    r"4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{"
    r"1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,"
    r"4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,"
    r"4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,"
    r"}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|("
    r"2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,"
    r"1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))"
)


@router.post("/")
async def add_ip(
    identifier: str,
    request: Request,
    ipv4_address: Optional[str] = None,
    ipv6_address: Optional[str] = None,
):
    if identifier.strip() == "":
        raise HTTPException(
            status_code=422, detail="Missing identifier query parameter"
        )
    if ipv4_address is None:
        if "cf-connecting-ip" in request.headers:
            ipv4_address = request.headers.get("cf-connecting-ip")
        else:
            ipv4_address = request.client.host
    if not ipv4_pattern.match(ipv4_address):
        raise HTTPException(status_code=422, detail="Invalid IP address format")
    if ipv6_address and not ipv6_pattern.match(ipv6_address):
        raise HTTPException(status_code=422, detail="Invalid IP address format")

    return __update_ip(identifier, ipv4_address, ipv6_address)


@router.get("/")
async def get_all_ips():
    with Session(engine) as s:
        rows = s.execute(select(IpAddress)).scalars().all()
        if len(rows) == 0:
            raise HTTPException(status_code=404, detail="No IP addresses found")
        return rows


@router.get("/{identifier}")
async def get_ip(identifier: str):
    with Session(engine) as s:
        stmt = select(IpAddress).where(IpAddress.id == identifier)
        row: IpAddress = s.execute(stmt).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Identifier not found")
        return row


def __update_ip(
    identifier: str, ipv4_address: Optional[str], ipv6_address: Optional[str]
):
    with Session(engine) as s:
        stmt = select(IpAddress).where(IpAddress.id == identifier)
        row: IpAddress = s.execute(stmt).scalar_one_or_none()
        if row is None:
            row = IpAddress(
                id=identifier,
                ipv4_address=ipv4_address,
                ipv6_address=ipv6_address,
                updated_at=datetime.datetime.now(),
            )
            s.add(row)
        else:
            row.ipv4_address = ipv4_address
            row.ipv6_address = ipv6_address
            row.updated_at = datetime.datetime.now()
        s.flush()
        s.commit()
        s.refresh(row)
        return row

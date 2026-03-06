from sqlalchemy import TIMESTAMP, Column, String

from database import Base


class IpAddress(Base):
    __tablename__ = "ip_address"

    id = Column(String, primary_key=True, nullable=False, index=True)
    ipv4_address = Column(String, nullable=False)
    ipv6_address = Column(String, nullable=True)
    updated_at = Column(TIMESTAMP, nullable=False)

import ipaddress
from typing import Optional

from pydantic import field_validator
from sqlmodel import Field, Relationship, SQLModel


class IpaddressBase(SQLModel):
    address: str
    reserved: bool = False
    description: Optional[str] = None


class Ipaddress(IpaddressBase, table=True):
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    subnet_id: int = Field(foreign_key="subnet.id")
    subnet: Optional["Subnet"] = Relationship(back_populates="ipaddresses")


class IpaddressRead(IpaddressBase):
    id: int
    subnet_id: int


class IpaddressCreate(IpaddressBase):
    subnet_id: int

    @field_validator("address")
    @classmethod
    def validate_address(cls, v):
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError(f"address {v} is not a valid ip address")
        return v


class IpaddressUpdate(IpaddressBase):
    description: Optional[str] = None


from pyipam.models.subnet import Subnet  # noqa

Subnet.update_forward_refs()

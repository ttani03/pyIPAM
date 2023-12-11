import ipaddress
from typing import Optional

from pydantic import field_validator, model_validator
from sqlmodel import Field, Relationship, SQLModel


class SubnetBase(SQLModel):
    name: str
    network: str
    gateway: Optional[str] = None
    nameserver: Optional[str] = None
    description: Optional[str] = None


class Subnet(SubnetBase, table=True):
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    ipaddresses: list["Ipaddress"] = Relationship(back_populates="subnet")


class SubnetRead(SubnetBase):
    id: int


class SubnetCreate(SubnetBase):
    @field_validator("network")
    @classmethod
    def validate_network(cls, v):
        try:
            ipaddress.ip_network(v)
        except ValueError:
            raise ValueError(f"network {v} is not a valid network")
        return v

    @field_validator("gateway")
    @classmethod
    def validate_gateway(cls, v):
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError(f"gateway {v} is not a valid network")
        return v

    @field_validator("nameserver")
    @classmethod
    def validate_nameserver(cls, v):
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError(f"nameserver {v} is not a valid network")
        return v

    @model_validator(mode="after")
    def validate_gateway_in_network(self):
        if self.gateway is None:
            return self
        network = ipaddress.ip_network(self.network)
        gateway = ipaddress.ip_address(self.gateway)
        if (
            gateway not in network
            or gateway == network.network_address
            or gateway == network.broadcast_address
        ):
            raise ValueError(f"gateway {gateway} is not valid in network {network}")
        return self


class SubnetUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None


from pyipam.models.ipaddress import Ipaddress  # noqa

Ipaddress.update_forward_refs()

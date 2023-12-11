import ipaddress

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm.exc import NoResultFound
from sqlmodel import Session, select

from pyipam.db.engine import get_session
from pyipam.models.ipaddress import Ipaddress
from pyipam.models.subnet import Subnet, SubnetCreate, SubnetRead

router = APIRouter()


@router.get("/subnets", response_model=list[SubnetRead])
async def read_subnets(*, session: Session = Depends(get_session)):
    """
    Retrieve a list of subnets.

    Parameters:
    - session: The database session.

    Returns:
    - A list of SubnetRead objects representing the subnets.
    """
    results = session.exec(select(Subnet)).all()
    return results


@router.get("/subnets/{subnet_id}", response_model=SubnetRead)
async def read_subnet(*, session: Session = Depends(get_session), subnet_id: int):
    """
    Retrieve a subnet by its ID.

    Args:
        session (Session): The database session.
        subnet_id (int): The ID of the subnet to retrieve.

    Returns:
        SubnetRead: The retrieved subnet.

    Raises:
        HTTPException: If the subnet with the specified ID is not found.
    """
    try:
        result = session.exec(select(Subnet).where(Subnet.id == subnet_id)).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"subnet_id {subnet_id} not found")
    return result


@router.post("/subnets", response_model=SubnetRead)
async def create_subnet(
    *, session: Session = Depends(get_session), subnet: SubnetCreate
):
    """
    Create a new subnet.

    Args:
        session (Session): The database session.
        subnet (SubnetCreate): The subnet data.

    Returns:
        SubnetRead: The created subnet.
    """
    subnet_db = Subnet.from_orm(subnet)
    session.add(subnet_db)

    # Create ipaddresses with subnet_id=subnet.id
    for ip in ipaddress.ip_network(subnet.network).hosts():
        ipaddress_db = Ipaddress(
            address=str(ip), reserved=False, description=None, subnet=subnet_db
        )
        if subnet.gateway is not None and ip == ipaddress.ip_address(subnet.gateway):
            ipaddress_db.reserved = True
            ipaddress_db.description = "gateway"
        session.add(ipaddress_db)
    session.commit()

    return subnet_db


@router.delete("/subnets/{subnet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subnet(
    *, session: Session = Depends(get_session), subnet_id: int, force: bool = False
):
    """
    Delete a subnet by its ID.

    Args:
        session (Session): The database session.
        subnet_id (int): The ID of the subnet to delete.
        force (bool, optional): Whether to force delete the subnet even if it has IP addresses with reserved flag set to True. Defaults to False.

    Raises:
        HTTPException: If the subnet with the specified ID is not found or if it has IP addresses with reserved flag set to True.

    Returns:
        None
    """
    # Check if subnet exists
    subnet = session.exec(select(Subnet).where(Subnet.id == subnet_id)).one()
    if not subnet:
        raise HTTPException(status_code=404, detail=f"subnet_id {subnet_id} not found")

    # Check if subnet has ipaddresses with reserved is True
    ipaddresses = session.exec(
        select(Ipaddress).where(Ipaddress.subnet_id == subnet_id)
    ).all()
    if not force:
        for ip in ipaddresses:
            if ip.reserved:
                raise HTTPException(
                    status_code=400,
                    detail=f"subnet_id {subnet_id} has ipaddresses with reserved is True",
                )

    # Delete ipaddresses
    for ip in ipaddresses:
        session.delete(ip)

    # Delete subnet
    session.delete(subnet)
    session.commit()

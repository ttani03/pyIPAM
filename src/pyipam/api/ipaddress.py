from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm.exc import NoResultFound
from sqlmodel import Session, select

from pyipam.db.engine import get_session
from pyipam.models.ipaddress import Ipaddress, IpaddressRead

router = APIRouter()


@router.get("/ipaddresses", response_model=list[IpaddressRead])
async def read_ipaddresses(
    *,
    session: Session = Depends(get_session),
    reserved: bool | None = None,
):
    """
    Retrieve a list of IP addresses.

    Args:
        session (Session): The database session.
        reserved (bool | None, optional): Filter IP addresses by reservation status. Defaults to None.

    Returns:
        list[IpaddressRead]: A list of IP addresses.
    """
    if reserved is not None:
        statement = select(Ipaddress).where(Ipaddress.reserved == reserved)
    else:
        statement = select(Ipaddress)

    results = session.exec(statement).all()
    return results


@router.get("/subnets/{subnet_id}/ipaddresses", response_model=list[IpaddressRead])
async def read_ipaddresses_by_subnet(
    *,
    session: Session = Depends(get_session),
    subnet_id: int,
    reserved: bool | None = None,
):
    """
    Retrieve a list of IP addresses by subnet ID.

    Args:
        session (Session): The database session.
        subnet_id (int): The ID of the subnet.
        reserved (bool | None, optional): Filter IP addresses by reservation status. Defaults to None.

    Returns:
        list[IpaddressRead]: A list of IP addresses matching the given subnet ID and reservation status.
    """
    if reserved is not None:
        statement = select(Ipaddress).where(
            Ipaddress.subnet_id == subnet_id, Ipaddress.reserved == reserved
        )
    else:
        statement = select(Ipaddress).where(Ipaddress.subnet_id == subnet_id)

    try:
        results = session.exec(statement).all()
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"subnet_id {subnet_id} not found")
    return results


@router.post("/subnets/{subnet_id}/ipaddresses", response_model=IpaddressRead)
async def reserve_ipaddress(
    *,
    session: Session = Depends(get_session),
    subnet_id: int,
):
    """
    Reserves an available IP address from the specified subnet.

    Args:
        session (Session): The database session.
        subnet_id (int): The ID of the subnet.

    Returns:
        IpaddressRead: The reserved IP address.

    Raises:
        HTTPException: If the subnet with the specified ID is not found or if there are no available IP addresses.
    """
    statement = select(Ipaddress).where(
        Ipaddress.subnet_id == subnet_id,
        Ipaddress.reserved == False,  # noqa
    )
    try:
        ipaddress = session.exec(statement).first()
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"subnet_id {subnet_id} not found")

    if ipaddress is None:
        raise HTTPException(status_code=404, detail="no available ipaddresses")

    ipaddress.reserved = True
    session.add(ipaddress)
    session.commit()
    session.refresh(ipaddress)
    return ipaddress


@router.delete("/ipaddresses/{ipaddress_id}", status_code=status.HTTP_204_NO_CONTENT)
async def free_ipaddress(
    *,
    session: Session = Depends(get_session),
    ipaddress_id: int,
):
    """
    Free an IP address by setting its 'reserved' flag to False.

    Args:
        session (Session): The database session.
        ipaddress_id (int): The ID of the IP address to free.

    Returns:
        dict: A dictionary with the status of the operation.
    """
    statement = select(Ipaddress).where(Ipaddress.id == ipaddress_id)
    try:
        ipaddress = session.exec(statement).first()
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail=f"ipaddress_id {ipaddress_id} not found"
        )

    if ipaddress is None:
        raise HTTPException(status_code=404, detail="ipaddress not found")

    ipaddress.reserved = False
    session.add(ipaddress)
    session.commit()

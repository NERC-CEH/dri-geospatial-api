import ipaddress
import logging

from fastapi import Depends, HTTPException, Request

from geospatial_api.config import setup_config

logger = logging.getLogger(__name__)

config = setup_config()

WHITELISTED_IPS = [ipaddress.ip_network(ip.strip(), strict=False) for ip in config.whitelisted_ips.split(",")]


def extract_client_ip_address(request: Request) -> str | None:
    """Extract the IP address from the request header.

    When requests come through the ALB, the IP address sits under the
    X-Forwarded-For attribute, and also gets appended to the IP address
    from the load balancer. Hence, we have to extract the rightmost IP address.
    Read the rightmost IP from X-Forwarded-For — this is the IP appended. All our
    traffic comes through the ALB except when running locally, which is the fallback option.

    Args:
        request: The FastAPI request object

    Returns:
        The IP address if there is one, None if there isnt.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[-1].strip()

    if request.client:
        return request.client.host

    return None


def check_ip_address_allowed(ip_address: str, whitelisted_ips: list) -> bool:
    """Check the IP address is within the whitelisted IP addresses.

    Args
        ip_address: The IP address
        whitelisted_ips: A list of whitelisted ip addresses

    Raises:
        ValueError if IP address is malformed

    Returns:
        True if the IP is within any of the whitelisted networks, False if not.
    """
    try:
        return any(ipaddress.ip_address(ip_address) in network for network in whitelisted_ips)
    except ValueError:
        logger.warning(f"{ip_address!r} is not a valid IP address.")
        return False


def check_ip_address_is_whitelisted(request: Request) -> bool:
    """
    Check whether the client IP address is one of the whitelisted IP addresses (internal
    UKCEH). This would allow access to certain parts of endpoint requests that
    are otherwise blocked to the public.

    For example, the NRFA network should only be visible to UKCEH employees and
    not to the public.

    Args:
        request: The incoming request

    Returns:
        a boolean as to whether the IP address is in the accepted list of IP addresses
    """
    ip_address = extract_client_ip_address(request)

    if not ip_address:
        return False

    return check_ip_address_allowed(ip_address, WHITELISTED_IPS)


def require_whitelisted_ip_address(is_whitelisted: bool = Depends(check_ip_address_is_whitelisted)) -> None:
    """
    Block access to entire endpoints.

    Using the result from the IP address check, block access to the endpoint if the IP address
    isnt UKCEH internal. This differs to the IP address check in that it doesnt allow any access
    to the endpoint, whereas the IP address check will allow access to the endpoint but will
    then restrict what comes back in the request.

    This function also makes use of FastAPIs caching with dependencies which ensures the IP
    address check is only run once on each request.

    Args:
        is_whitelisted A boolean indicating whether the request is coming from UKCEH whitelisted
        IP addresses.

    Raises:
        HTTPException: If access to the ednpoint cannot be granted.
    """
    if not is_whitelisted:
        raise HTTPException(
            status_code=403,
            detail="Access denied: IP not in whitelist",
        )

"""Request security helpers shared by rate limits and audit events."""

import ipaddress

from django.conf import settings


def client_ip(request):
    """Return the client address without trusting arbitrary forwarded headers.

    ``X-Forwarded-For`` is considered only when the TCP peer is inside the
    explicitly configured trusted proxy CIDRs. Trusted hops are removed from
    right to left; malformed or oversized chains fall back to ``REMOTE_ADDR``.
    The edge proxy must overwrite or correctly append this header.
    """
    remote = _parse_ip(request.META.get('REMOTE_ADDR', ''))
    if remote is None:
        # A missing/invalid peer must not make a caller-controlled header the
        # source of identity. A stable sentinel fails closed for rate limits.
        return '0.0.0.0'

    trusted_proxies = _trusted_proxy_networks()
    if not any(remote in network for network in trusted_proxies):
        return remote.compressed

    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if not forwarded or len(forwarded) > 1024:
        return remote.compressed
    raw_hops = [value.strip() for value in forwarded.split(',')]
    if len(raw_hops) > 20:
        return remote.compressed
    hops = [_parse_ip(value) for value in raw_hops]
    if not hops or any(hop is None for hop in hops):
        return remote.compressed

    chain = hops + [remote]
    while len(chain) > 1 and any(chain[-1] in network for network in trusted_proxies):
        chain.pop()
    return chain[-1].compressed


def _parse_ip(value):
    try:
        return ipaddress.ip_address(value)
    except (TypeError, ValueError):
        return None


def _trusted_proxy_networks():
    networks = []
    for value in getattr(settings, 'MATCHCO_TRUSTED_PROXY_CIDRS', ()):
        try:
            networks.append(ipaddress.ip_network(value, strict=False))
        except ValueError:
            # An invalid proxy entry must never widen trust; ignore it.
            continue
    return networks

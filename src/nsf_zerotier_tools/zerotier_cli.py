"""Zerotier restapi client command line interface"""
from typing import Optional
from dataclasses import dataclass
import click
import logging
import datetime
import warnings
import sys
from .zerotier import ZtClient, ZtNetworkService, compute_human_readable_last_seen_str

LOGGER = logging.getLogger(__name__)


@dataclass
class CliContext:
    """Click cli app context."""
    client: ZtClient


@dataclass
class CliNetworkContext:
    """Click cli app network group context."""
    network: ZtNetworkService


def composed(*decs):
    def deco(f):
        for dec in reversed(decs):
            f = dec(f)
        return f
    return deco


def _get_network_shared_options():
    return [
        click.option(
            '-v', '--verbose', default=0, count=True,
            help="Verbosity level."),
        click.option(
            '--api-token', envvar='NSF_ZEROTIER_API_TOKEN',
            prompt=True, hide_input=True,
            help=(
                "Zerotier api access token as can be "
                "managed from <https://my.zerotier.com/> *Account* tab.")),
        click.option(
            '--network-id', envvar='NSF_ZEROTIER_NETWORK_ID',
            prompt=True,
            help=(
                "Network id as can be obtained "
                "from <https://my.zerotier.com/> *Network* tab."))
    ]


def network_shared_options(func):
    options = _get_network_shared_options()
    return composed(*options)(func)


def network_member_shared_options(func):
    options = _get_network_shared_options()
    options.extend([
        click.option(
            '--member-id', envvar='NSF_ZEROTIER_MEMBER_ID',
            prompt=True,
            help=(
                "Network member id as output (3rd field) when calling "
                "``zerotier-cli`` on the device (requires root priviledges)."))
    ])
    return composed(*options)(func)


def setup_verbose(
        verbose: int) -> None:
    verbosity_mapping = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
    }
    assert verbose >= 0
    logging.basicConfig(
        level=verbosity_mapping.get(verbose, logging.DEBUG))


def setup_shared_network_options(
        verbose: int,
        api_token: str,
        network_id: str
) -> CliNetworkContext:
    setup_verbose(verbose)

    # create client and set the authentication header
    client = ZtClient(api_token)
    network = client.get_network_service(network_id)

    return CliNetworkContext(
        network=network)


@click.group()
def cli() -> None:
    """A Zerotier restapi client."""
    pass


@cli.group()
def network() -> None:
    """Zerotier network related commands."""
    pass


@network.group()
def member() -> None:
    """Zerotier network members related commands."""
    pass


@member.command()
@network_shared_options
@click.option(
    '--name',
    help="Filter results by *short name*.")
@click.option(
    '--description',
    help="Filter results by *description*.")
@click.option(
    '--authorized/--deauthorized', default=None,
    help="List only autorized / deauthorized members.")
@click.option(
    '--online/--offline', default=None,
    help="List only online / offline members.")
def ls(
        verbose: int,
        api_token: str,
        network_id: str,
        name: Optional[str],
        description: Optional[str],
        authorized: Optional[bool],
        online: Optional[bool],
) -> None:
    """List Zerotier members of specified network."""

    # IDEA: Sort by last-seen flag.

    obj = setup_shared_network_options(
        verbose, api_token, network_id)
    network = obj.network
    members = network.get_network_members()

    for m in members:
        last_seen_str = compute_human_readable_last_seen_str(
            m.last_online, m.online)

        if name is not None and not (name in m.name):
            continue

        if description is not None and not (description in m.description):
            continue

        if authorized is not None and not (authorized == m.authorized):
            continue

        if online is not None and not (online == m.online):
            continue

        print((
            "auth: {}, id: {}, ip: {}, name: \"{}\", "
            "last-seen: \"{}\", phys-ip: {}, desc: \"{}\"").format(
            m.authorized, m.member_id, m.managed_ips, m.name,
            last_seen_str, m.physical_ip, m.description))


class InsufficientPriviledgesWarning(UserWarning):
    pass


def simply_format_warning(
        message: str, category, filename, lineno, file=None, line=None):
    if file is None:
        file = sys.stderr

    # category.__name__
    print("WARNING: {}".format(message),
        file=file)


@member.command()
@network_member_shared_options
@click.option(
    '--name', default=None,
    help=(
        "A human readable short name to be given to "
        "this member. Ideally unique."))
@click.option(
    '--description', default=None,
    help="A longer description to be given to this member.")
def authorize(
        verbose: int,
        api_token: str,
        network_id: str,
        member_id: str,
        name: Optional[str],
        description: Optional[str]
) -> None:
    """Authorize Zerotier network member to the network."""
    obj = setup_shared_network_options(
        verbose, api_token, network_id)

    network = obj.network

    with warnings.catch_warnings():
        warnings.showwarning = simply_format_warning
        if not network.permissions.modify and name is not None:
            warnings.warn(InsufficientPriviledgesWarning(
                "Insufficient privileges to 'modify' network member 'name' field. "
                "Proceding with member authorization."))
            name = None

        if not network.permissions.modify and description is not None:
            warnings.warn(InsufficientPriviledgesWarning(
                "Insufficient privileges to 'modify' network member 'description' field. "
                "Proceding with member authorization."))
            description = None

    network.update_member(
        member_id,
        authorized=True,
        name=name,
        description=description)


@member.command()
@network_member_shared_options
def deauthorize(
        verbose: int,
        api_token: str,
        network_id: str,
        member_id: str
) -> None:
    """Deauthorize Zerotier network member from the network."""

    # IDEA: Support deauth by short name at some point.
    obj = setup_shared_network_options(
        verbose, api_token, network_id)
    network = obj.network
    network.update_member(
        member_id,
        authorized=False)


@member.command()
@network_member_shared_options
@click.option(
    '--authorized/--deauthorized', default=None,
    help=(
        "A human readable short name to be given to "
        "this member. Ideally unique."))
@click.option(
    '--name', default=None,
    help=(
        "A human readable short name to be given to "
        "this member. Ideally unique."))
@click.option(
    '--description', default=None,
    help="A longer description to be given to this member.")
def modify(
        verbose: int,
        api_token: str,
        network_id: str,
        member_id: str,
        authorized: Optional[bool],
        name: Optional[str],
        description: Optional[str]
) -> None:
    """Edit Zerotier network member information."""
    obj = setup_shared_network_options(
        verbose, api_token, network_id)
    network = obj.network
    network.update_member(
        member_id,
        authorized=authorized,
        name=name,
        description=description)


if __name__ == "__main__":
    cli()

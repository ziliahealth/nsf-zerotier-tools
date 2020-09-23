from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from zerotier import client as ztclient

@dataclass(frozen=True)
class ZtNetworkMemberEntry:
    """Zerotier network member."""
    authorized: bool
    member_id: str
    name: str
    managed_ips: List[str]
    physical_ip: str
    last_online: datetime
    online: bool
    description: str


@dataclass(frozen=True)
class ZtNetworkPermissions:
    """Zerotier network permissions."""
    read: bool
    authorize: bool
    modify: bool
    delete: bool


@dataclass(frozen=True)
class ZtNetworkEntry:
    id: str
    current_user_permissions: ZtNetworkPermissions


@dataclass(frozen=True)
class ZtUserEntry:
    id: str
    email: str


@dataclass(frozen=True)
class ZtStatusEntry:
    current_user: ZtUserEntry
    version: str
    api_version: int


class ZtClient:
    """Zerotier app specific client."""
    def __init__(self, api_token: str) -> None:
        self._client = ztclient.Client()
        self._client.set_auth_header("Bearer " + api_token)
        self._status = self.get_status()

    def _get_self_json(self) -> Dict[str, Any]:
        # This is broken when using token auth.
        response = self._client.self.getAuthenticatedUser()
        response_json = response.json()
        # assert "Network" == response_json["type"]
        return response_json

    def _get_status_json(self) -> Dict[str, Any]:
        response = self._client.status.getStatus()
        response_json = response.json()
        assert "CentralStatus" == response_json["type"]
        return response_json

    def get_status(self) -> ZtStatusEntry:
        status_json = self._get_status_json()

        current_user_json = status_json["user"]
        assert "User" == current_user_json["type"]

        current_user = ZtUserEntry(
            id=current_user_json["id"],
            email=current_user_json["email"]
        )

        status = ZtStatusEntry(
            current_user=current_user,
            version=status_json["version"],
            api_version=status_json["apiVersion"],
        )
        return status

    def _get_network_json(self, network_id: str) -> Dict[str, Any]:
        response = self._client.network.getNetwork(network_id)
        response_json = response.json()
        assert "Network" == response_json["type"]
        return response_json

    def get_network(self, network_id: str) -> ZtNetworkEntry:
        network_json = self._get_network_json(network_id)
        current_user_id = self._status.current_user.id
        current_user_perm_json = network_json["permissions"][current_user_id]

        current_user_perm = ZtNetworkPermissions(
            read=current_user_perm_json["r"],
            authorize=current_user_perm_json["a"],
            modify=current_user_perm_json["m"],
            delete=current_user_perm_json["d"]
        )
        return ZtNetworkEntry(
            id=network_json["id"],
            current_user_permissions=current_user_perm
        )

    def get_network_service(self, network_id: str) -> 'ZtNetworkService':
        network = self.get_network(network_id)
        return ZtNetworkService(self._client.network, network)


class ZtNetworkService:
    def __init__(
            self,
            service: ztclient.NetworkService,
            network_entry: ZtNetworkEntry
    ) -> None:
        self._service = service
        self._network_entry = network_entry
        self._id = network_entry.id

    @property
    def permissions(self):
        return self._network_entry.current_user_permissions

    @staticmethod
    def _make_datetime_from_api_timestamp(
            timestamp_msec_since_epoch: int) -> datetime:
        return datetime.fromtimestamp(
            float(timestamp_msec_since_epoch / 1000))

    def _get_network_members_json(
            self) -> List[Dict[str, Any]]:
        members = self._service.listMembers(self._id).json()
        return members

    @classmethod
    def _make_network_member_from_json(
            cls, member_json: Dict[str, Any]
    ) -> ZtNetworkMemberEntry:
        m = member_json
        assert "Member" == m["type"]
        cfg_section = m["config"]

        last_online = cls._make_datetime_from_api_timestamp(
            m["lastOnline"])

        return ZtNetworkMemberEntry(
            authorized=cfg_section["authorized"],
            member_id=m["nodeId"],
            name=m["name"],
            managed_ips=cfg_section["ipAssignments"],
            physical_ip=m["physicalAddress"],
            last_online=last_online,
            online=m["online"],
            description=m["description"]
        )

    def get_network_members(
            self
    ) -> List[ZtNetworkMemberEntry]:
        members_json = self._get_network_members_json()

        out = []
        for m in members_json:
            assert "Member" == m["type"]
            member = self._make_network_member_from_json(m)
            out.append(member)
        return out

    def _get_member_json(
            self, member_id: str
    ) -> Dict[str, Any]:
        response = self._service.getMember(member_id, self._id)
        response_json = response.json()
        assert "Member" == response_json["type"]
        return response_json

    def get_member(
            self, member_id: str
    ) -> ZtNetworkMemberEntry:
        member_json = self._get_member_json(member_id)
        return self._make_network_member_from_json(member_json)

    def _update_network_member_json(
            self,
            member_id: str,
            authorized: Optional[bool] = None,
            name: Optional[str] = None,
            description: Optional[str] = None,
    ) -> Dict[str, Any]:
        cfg_fields_diff: Dict[str, Any] = dict()
        if authorized is not None:
            cfg_fields_diff.update({'authorized': authorized})

        fields_diff: Dict[str, Any] = dict()
        if cfg_fields_diff:
            fields_diff.update({'config': cfg_fields_diff})
        if name is not None:
            fields_diff.update({'name': name})
        if description is not None:
            fields_diff.update({'description': description})


        # member_json = self._get_member_json(network_id, member_id)
        member_json = dict()
        member_json.update(fields_diff)
        member_json['config'].update(cfg_fields_diff)
        response = self._service.updateMember(
            member_json, member_id, self._id)
        response_json = response.json()
        assert "Member" == response_json["type"]
        return response_json

    def update_member(
            self,
            member_id: str,
            authorized: Optional[bool] = None,
            name: Optional[str] = None,
            description: Optional[str] = None,
    ) -> ZtNetworkMemberEntry:
        member_json = self._update_network_member_json(
            member_id,
            authorized,
            name,
            description)

        return self._make_network_member_from_json(member_json)



def compute_last_seen(
        last_online_t: datetime
) -> timedelta:
    now_t = datetime.now()
    last_seen_td = now_t - last_online_t
    return last_seen_td


def compute_human_readable_last_seen_str(
        last_online_t: datetime, online: bool
) -> str:
    if online:
        return "ONLINE"
    last_seen_td = compute_last_seen(last_online_t)

    d = last_seen_td.days
    h, rs = divmod(last_seen_td.seconds, 3600)
    m, s = divmod(last_seen_td.seconds, 60)

    d_str = "" if 0 == d else "{}d ".format(d)
    h_str = "" if 0 == h else "{}h ".format(h)
    m_str = "" if 0 == m else "{}m ".format(m)
    s_str = "" if 0 == s else "{}s".format(s)
    last_seen_str = str("{}{}{}{}".format(d_str, h_str, m_str, s_str))
    return last_seen_str

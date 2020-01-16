from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from zerotier import client as ztclient


@dataclass(frozen=True)
class ZtNetworkMemberEntry:
    """Zero tier network member."""
    authorized: bool
    member_id: str
    name: str
    managed_ips: List[str]
    physical_ip: str
    last_online: datetime
    online: bool
    description: str


class ZeroTierClient:
    """Zerotier app specific client."""
    def __init__(self, api_token: str) -> None:
        self._client = ztclient.Client()
        self._client.set_auth_header("Bearer " + api_token)

    @staticmethod
    def _make_datetime_from_api_timestamp(
            timestamp_msec_since_epoch: int) -> datetime:
        return datetime.fromtimestamp(
            float(timestamp_msec_since_epoch / 1000))

    def _get_network_members_json(
            self, network_id: str) -> List[Dict[str, Any]]:
        client = self._client
        network = client.network.getNetwork(network_id).json()
        members = client.network.listMembers(network['id']).json()
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
            self, network_id: str
    ) -> List[ZtNetworkMemberEntry]:
        members_json = self._get_network_members_json(network_id)

        out = []
        for m in members_json:
            assert "Member" == m["type"]
            member = self._make_network_member_from_json(m)
            out.append(member)
        return out

    def _get_member_json(
            self, network_id: str, member_id: str
    ) -> Dict[str, Any]:
        response = self._client.network.getMember(member_id, network_id)
        response_json = response.json()
        assert "Member" == response_json["type"]
        return response_json

    def get_member(
            self, network_id: str, member_id: str
    ) -> ZtNetworkMemberEntry:
        member_json = self._get_member_json(network_id, member_id)
        return self._make_network_member_from_json(member_json)

    def _update_network_member_json(
            self, network_id: str, member_id: str,
            authorized: Optional[bool] = None,
            name: Optional[str] = None,
            description: Optional[str] = None,
    ) -> Dict[str, Any]:
        cfg_fields_diff = dict()
        if authorized is not None:
            cfg_fields_diff.update({'authorized': authorized})

        fields_diff = dict()
        if name is not None:
            fields_diff.update({'name': name})
        if description is not None:
            fields_diff.update({'description': description})


        member_json = self._get_member_json(network_id, member_id)
        member_json.update(fields_diff)
        member_json['config'].update(cfg_fields_diff)
        response = self._client.network.updateMember(
            member_json, member_id, network_id)
        response_json = response.json()
        assert "Member" == response_json["type"]
        return response_json

    def update_network_member(
            self, network_id: str, member_id: str,
            authorized: Optional[bool] = None,
            name: Optional[str] = None,
            description: Optional[str] = None,
    ) -> ZtNetworkMemberEntry:
        member_json = self._update_network_member_json(
            network_id, member_id,
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

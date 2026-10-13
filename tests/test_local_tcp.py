"""VIEW-compatible local TCP signaling, tested only against a loopback peer."""
import asyncio
from unittest.mock import AsyncMock

import pytest
from harness.peer import is_
from harness.rig import Rig, run, wait_until

from custom_components.vimar_intercom import runtime as R
from custom_components.vimar_intercom import sip_client as sip


@pytest.mark.parametrize("local, transport, expected", [
    (True, "udp", "UDP"), (True, "tcp", "TCP"), (False, "tcp", "TLS"),
    (True, "unknown", "UDP"),
])
def test_transport_configuration_preserves_legacy_domains(local, transport, expected):
    R.configure({"use_local_udp": local, "local_transport": transport,
                 "local_domain": "local.example.test", "cloud_domain": "cloud.example.test",
                 "sip_user": "10101", "camera_target": "20202"})
    domain = "local.example.test" if local else "cloud.example.test"
    assert R.SIP_DOMAIN == domain
    assert R.INTERCOM == f"sip:20202@{domain}"
    assert sip._transport() == expected
    assert R.use_udp() is (expected == "UDP")


def test_old_entries_still_use_udp():
    R.configure({"use_local_udp": True})
    assert R.LOCAL_TRANSPORT == "udp" and R.use_udp()


@pytest.mark.parametrize("record_route", [False, True])
def test_tcp_registration_outgoing_and_incoming_call_routing(monkeypatch, record_route):
    async def scenario():
        async with Rig(monkeypatch, "tcp") as rig:
            peer = rig.peer
            if not record_route:
                peer.record_route = ""
            peer.strict_route = record_route
            await rig.register()
            assert rig.hub.transport == "tcp-local"
            regs = peer.got(is_("REGISTER"))
            assert len(regs) == 2 and "authorization" in regs[1].hdrs
            endpoint = sip.writer.get_extra_info("sockname")
            for msg in regs:
                assert f"SIP/2.0/TCP {endpoint[0]}:{endpoint[1]};alias;" in msg.h("via")
                assert f"@{endpoint[0]}:{endpoint[1]};transport=tcp>" in msg.h("contact")
                assert ";expires=900" in msg.h("contact")
                assert msg.h("route") == "<sip:127.0.0.1;transport=tcp;lr>"
                assert "pn-tok" not in msg.raw and "transport=tls" not in msg.raw
            rig.answer()
            ok, _ = await sip.do_call()
            assert ok and sip.in_call
            invite = peer.got(is_("INVITE"))[0]
            assert invite.first.split()[1] == R.INTERCOM
            assert invite.h("route") == regs[0].h("route")
            assert "transport=tcp" in invite.h("contact")
            await sip.do_hangup()
            bye = peer.got(is_("BYE"))[-1]
            assert bye.first.split()[1] == peer.contact_uri
            assert bye.h("route") == peer.record_route
            assert not peer.dropped
            rig.ring("synthetic-tcp-ring")
            await peer.wait_for(is_(code=183), timeout=3)
            assert sip.ringing()
            assert rig.rings
            assert await sip.do_answer_incoming()
            answer = await peer.wait_for(is_(code=200, cseq="INVITE"), timeout=3)
            assert "transport=tcp" in answer.h("contact")
            await sip.do_hangup()
    run(scenario())


def test_tcp_does_not_retransmit_datagrams_or_fall_back_to_cloud(monkeypatch):
    async def scenario():
        async with Rig(monkeypatch, "tcp") as rig:
            await rig.register()
            monkeypatch.setattr(sip, "_T1", 0.01)
            rig.peer.silent.add("OPTIONS")
            assert not await sip._send_request(
                "OPTIONS sip:local.example.test SIP/2.0\r\nCall-ID: synthetic-options\r\n"
                "CSeq: 1 OPTIONS\r\nContent-Length: 0\r\n\r\n", "synthetic-options", timeout=0.06)
            assert len(rig.peer.got(is_("OPTIONS"))) == 1
            rig.peer.on_invite = AsyncMock()  # Receives INVITE, sends no response.
            ok, _ = await sip.do_call(answer_timeout=0.06)
            assert not ok
            assert len(rig.peer.got(is_("INVITE"))) == 1
            cloud = AsyncMock(side_effect=AssertionError("local reconnect attempted cloud push registration"))
            monkeypatch.setattr(sip, "do_connect_profiles", cloud)
            before = len(rig.peer.log)
            rig.peer.drop()
            await wait_until(lambda: not sip.registered, 3)
            await rig.peer.wait_for(is_("REGISTER"), timeout=8, start=before)
            await wait_until(lambda: sip.registered, 5)
            assert rig.peer.connections == 2 and R.USE_LOCAL_UDP
            cloud.assert_not_called()
            assert R.LOCAL_TRANSPORT == "tcp"
    run(scenario())


def test_tcp_connect_uses_local_endpoint_without_tls_or_cloud_dns(monkeypatch):
    async def scenario():
        monkeypatch.setattr(R, "USE_LOCAL_UDP", True)
        monkeypatch.setattr(R, "LOCAL_TRANSPORT", "tcp")
        monkeypatch.setattr(R, "LOCAL_PROXY", "127.0.0.1")
        monkeypatch.setattr(sip, "_resolve_sip_targets", lambda *args: pytest.fail("cloud DNS queried"))
        monkeypatch.setattr(sip, "_create_ssl_context", lambda *args: pytest.fail("TLS configured"))
        connection = AsyncMock(side_effect=OSError("synthetic connection failure"))
        monkeypatch.setattr(asyncio, "open_connection", connection)
        with pytest.raises(OSError, match="synthetic connection failure"):
            await sip.connect()
        connection.assert_awaited_once_with("127.0.0.1", sip.C.LOCAL_SIP_PORT)
        assert sip._my_port() == R.LOCAL_UDP_PORT
    run(scenario())

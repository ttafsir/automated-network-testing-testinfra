import pytest


def test_bgp_asn_matches_inventory(host, helpers, intended_config):
    """
    Arrange/Act: retrieve "ip bgp summary" output from device. Retrieve
        BGP intent from AVD intended design.
    Assert: The configured ASN matches the inventory ASN
    """
    if not intended_config.get("router_bgp"):
        pytest.xfail("BGP is not expected on this device")

    output = helpers.cli_command(host, "show ip bgp summary | json")
    actual = output["json"]["vrfs"]["default"]["asn"]
    expected = intended_config["router_bgp"]["as"]
    assert actual == expected


def test_bgp_multi_agent_is_configured(host, helpers, intended_config):
    """
    Arrange/Act: retrieve "ip route summary" output from device.
    Assert: The configured ArBGP multi-agent is enabled
    """
    if not intended_config.get("router_bgp") or not intended_config.get(
        "service_routing_protocols_model"
    ):
        pytest.xfail("BGP is not expected on this device")
    output = helpers.cli_command(host, "show ip route summary")
    assert "multi-agent" in output["stdout"]

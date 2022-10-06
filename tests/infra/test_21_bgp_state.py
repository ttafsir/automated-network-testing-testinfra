import pytest


def test_bgp_enabled(host, intended_config, helpers):
    """
    Arrange/Act: retrieve "show ip bgp summary" output from device.
    Assert: BGP process is enabled
    """
    if not intended_config.get("router_bgp"):
        pytest.xfail("BGP is not expected on this device")

    output = helpers.cli_command(host, "show ip bgp summary")
    assert "BGP is disabled" not in output


@pytest.mark.parametrize(
    "show_command",
    ["show ip bgp summary | json", "show bgp evpn summary | json"],
    ids=["bgp", "evpn"],
)
def test_bgp_expected_peers_are_established(
    host, helpers, show_command, intended_config
):
    """
    Arrange/Act: retrieve IPv4 and evpn BGP output from device. Retrieve
        BGP intent from AVD intended design.
    Assert: The configured expected peers are established for IPv4 and EVPN
    """
    if not intended_config.get("router_bgp"):
        pytest.xfail("BGP is not expected on this device")

    output = helpers.cli_command(host, show_command)
    actual = output["json"]["vrfs"]["default"]["peers"]
    expected = intended_config["router_bgp"]["neighbors"]
    assert (
        actual[neighbor]["peerState"] == "Established"
        for neighbor, _ in expected.items()
    )

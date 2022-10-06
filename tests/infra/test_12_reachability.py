from ipaddress import ip_interface

import pytest


def test_ethernet_link_neighbor_is_reachable(
    avd_p2p_link, get_host, helpers, get_config
):
    """
    Arrange: Load fabric p2p links and load device's structured configuration
    Act: Connect to device and ping from one end of the link to the other
    Assert: The link peer IPs are reachable on P2P links
    """
    # Arrange
    node_name = avd_p2p_link["Node"]
    node_interface = avd_p2p_link["Node Interface"]
    remote_ip = ip_interface(avd_p2p_link["Peer IP Address"])

    intended_config = get_config(node_name)
    source_ip = ip_interface(
        intended_config["ethernet_interfaces"][node_interface].get("ip_address")
    )

    # Act
    node = get_host(node_name)
    output = helpers.cli_command(
        node, f"ping {remote_ip.ip} source {source_ip.ip} repeat 1", check_mode=False
    )
    # Assert
    assert "1 received" in output["stdout"]


def test_remote_loopback0_reachability_from_l3leafs(
    host, host_vars, avd_fabric_loopback, helpers, get_config
):
    """
    Arrange: Retrieve configured loopback0 IPs from inventory
    Act: Ping each loopback IP from loopback0
    Assert: All loopback0 IPs can be reached from loopback0
    """
    if host_vars["type"] not in ("l3leaf"):
        pytest.skip(reason=f"Test is not applicable for {host_vars['type']}")

    hostname = host_vars["inventory_hostname"]
    intent = get_config(hostname)
    remote_ip = ip_interface(avd_fabric_loopback[1]["ip_address"])
    local_ip = ip_interface(intent["loopback_interfaces"]["Loopback0"]["ip_address"])
    # Act
    output = helpers.cli_command(
        host, f"ping {remote_ip.ip} source {local_ip.ip} repeat 1", check_mode=False
    )
    # Assert
    assert "1 received" in output["stdout"]

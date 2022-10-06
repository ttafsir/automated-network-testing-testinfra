import pytest


def test_every_link_in_avd_link_is_connected(avd_link, get_host, helpers):
    """
    Arrange/Act: Get device connection for link under test. Connect
        to the devices and gather "show interfaces" output
    Assert: Verify that link is connected
    """
    # Arrange
    hostname = avd_link["Node"]
    node_interface = avd_link["Node Interface"]

    # Act
    node = get_host(hostname)
    host_vars = helpers.get_hostvars(node)
    output = helpers.get_interface_facts(node, host_vars["ansible_network_os"])

    # Report Ansible Errors if Act failed
    try:
        node_interfaces = output["ansible_facts"]["ansible_net_interfaces"]
    except KeyError:
        pytest.fail(output.get("msg"))

    # Assert
    assert node_interfaces[node_interface]["operstatus"] == "connected"


def test_lldp_neighbors_match_intent(avd_p2p_link, get_host, helpers):
    """
    Arrange/Act: Get device connection for link under test. Get
        link's intended peer data. Connect to the devices and
        gather "show lldp neighbors" output
    Assert: Verify that the expected peer and port are found
    """
    # Arrange
    hostname = avd_p2p_link["Node"]
    node_interface = avd_p2p_link["Node Interface"]
    peer_node = avd_p2p_link["Peer Node"]
    peer_interface = avd_p2p_link["Peer Interface"]

    peer_type = avd_p2p_link["Peer Type"]
    if peer_type == "server":
        pytest.skip(reason="LLDP is not properly configured on servers")

    # Act
    node = get_host(hostname)
    host_vars = helpers.get_hostvars(node)
    output = helpers.get_interface_facts(node, host_vars["ansible_network_os"])

    # Assert
    if neighbor_facts := output["ansible_facts"].get("ansible_net_neighbors"):
        neighbors = [
            (link["host"], link["port"])
            for link in neighbor_facts.get(node_interface, [])
        ]

        # Assert that the expected neighbor is in the list of neighbors
        assert (peer_node, peer_interface) in neighbors

    else:
        pytest.fail(f"No neighbors found on: {node_interface}.\n{output.get('msg')}")


def test_l3_p2p_links_have_correct_ips(avd_p2p_link, get_host, helpers):
    """
    Arrange/Act: Get device connection for link under test. Connect
        to the devices and gather "show ip interface" output
    Assert: Verify that link has an IP address
    """
    # Arrange
    left_node = [
        avd_p2p_link["Node"],
        avd_p2p_link["Node Interface"],
        avd_p2p_link["Leaf IP Address"],
    ]

    right_node = [
        avd_p2p_link["Peer Node"],
        avd_p2p_link["Peer Interface"],
        avd_p2p_link["Peer IP Address"],
    ]

    # Let's loop through each side of the link, connect to the device on that side
    # and verify that the IP matches our intended state.
    for hostname, intf, ip in (left_node, right_node):
        node = get_host(hostname)
        host_vars = helpers.get_hostvars(node)

        # Act
        output = helpers.get_interface_facts(node, host_vars["ansible_network_os"])
        try:
            interface_facts = output["ansible_facts"]["ansible_net_interfaces"]
        except KeyError:
            pytest.fail(output.get("msg"))

        # Assert: Does the IP match our design?
        assert interface_facts[intf]["ipv4"]["address"] == ip.split("/")[0]
        assert int(interface_facts[intf]["ipv4"]["masklen"]) == int(ip.split("/")[1])

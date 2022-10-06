def test_hostname_matches_inventory(facts, host_vars):
    """
    Arrange/Act: Retrieve facts from device and variables from inventory
    Assert: The configured hostname matches the inventory hostname
    """
    actual = facts["ansible_facts"]["ansible_net_hostname"]
    expected = host_vars["inventory_hostname"]
    assert actual == expected


def test_software_version(facts, host_vars):
    """
    Arrange/Act: Retrieve facts from device and variables from inventory
    Assert: The current matches the inventory version

    Note: The expected version is expected in this format: 4.28.0F
          The device returns the full version detail:
            4.28.0F-26864689.4280F (engineering build)
    """
    actual = facts["ansible_facts"]["ansible_net_version"]
    expected = host_vars["version"]
    assert actual.startswith(expected)

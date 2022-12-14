def test_ntp_is_synchronised(host, helpers):
    """
    Arrange/Act: Retrieve facts from device and variables from inventory
    Assert: The configured ASN matches the inventory ASN
    """
    output = helpers.cli_command(host, "show ntp status | json")
    assert output["json"]["status"] == "synchronised", "NTP is not synchronised"

import pytest


def test_vlans_match_intent(host, host_vars, intended_config, helpers):
    """
    Arrange/Act: retrieve "show vlan | json" output from device.
    Assert: Every VLAN from the intended config is deployed to the device.
    """
    if host_vars["type"] == "spine":
        pytest.xfail(reason="No VLANs are expected on this device")

    # Arrange
    intended_vlans = intended_config.get("vlans")

    # Act/Assert
    output = helpers.cli_command(host, "show vlan | json", check_mode=False)
    vlan_ids = [int(k) for k, _ in output["json"]["vlans"].items()]
    intended_vlan_ids = [int(k) for k, _ in intended_vlans.items()]

    assert all(
        vlan in vlan_ids for vlan in intended_vlan_ids
    ), f"expected: {intended_vlan_ids}. Found: {vlan_ids}. Diff: {set(intended_vlan_ids).difference(vlan_ids)}"

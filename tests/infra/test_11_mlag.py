import pytest

# We can apply marks at the module level with the `pytestmark`` global variable.
# You can use a single marker or a list of markers.
# pytestmark = pytest.mark.eos
# pytestmark = [pytest.mark.eos, pytest.mark.mlag]


@pytest.mark.parametrize(
    "key, expected_value",
    [
        ("state", "active"),
        ("negStatus", "connected"),
    ],
)
def test_mlag_state_and_status(host, host_vars, helpers, key, expected_value):
    """
    Arrange/Act: Retrieve mlag operational state from device
    Assert: MLAG is active and connected on l2 and l3 leafs
    """
    if host_vars["type"] not in ("l2leaf", "l3leaf"):
        pytest.xfail(f"MLAG is not expected on {host_vars['type']} device")

    # Act
    output = helpers.cli_command(host, "show mlag detail | json")
    json_output = output.get("json")

    # Assert
    assert json_output[key] == expected_value


def test_mlag_configuration_matches_intent(host, host_vars, helpers, intended_config):
    """
    Arrange: Load intent for leaf devices
    Act: Retrieve mlag configuration state from leaf
    Assert: MLAG configuration matches intended configuration
    """
    if host_vars["type"] not in ("l2leaf", "l3leaf"):
        pytest.xfail(f"MLAG is not expected on {host_vars['type']} device")

    mlag_intent = intended_config.get("mlag_configuration")

    output = helpers.cli_command(host, "show mlag detail | json")
    json_output = output.get("json")

    assert (
        json_output["domainId"] == mlag_intent["domain_id"]
        and json_output["localInterface"] == mlag_intent["local_interface"]
        and json_output["peerLink"] == mlag_intent["peer_link"]
        and json_output["peerAddress"] == mlag_intent["peer_address"]
        and json_output["reloadDelay"] == mlag_intent["reload_delay_mlag"]
        and json_output["reloadDelayNonMlag"] == mlag_intent["reload_delay_non_mlag"]
    )

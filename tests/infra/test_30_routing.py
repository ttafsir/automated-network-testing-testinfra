import ipaddress

import pytest


def test_vtep_ip_in_routing_table(host, helpers, host_vars, vtep_intent):
    """
    Arrange/Act:
    """
    if host_vars["type"] == "l2leaf":
        pytest.skip(reason="Test is not applicable on l2leafs")

    vtep_address = ipaddress.IPv4Interface(vtep_intent[1])
    command = f"show ip route {vtep_address.ip}"
    output = helpers.cli_command(host, command, check_mode=False)
    assert f"{vtep_address}" in output["stdout"]

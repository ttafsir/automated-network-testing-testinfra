import logging
import typing as t
from functools import lru_cache
from pathlib import Path

import pytest
import testinfra

from tests.framework import load_avd_fabric_data, load_avd_structured_configs

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)
FACTS_MODULES = {"eos": "arista.eos.eos_facts", "ios": "cisco.ios.ios_facts"}


@pytest.fixture(scope="module", name="facts")
def facts_fixture(host):
    """Retrieve facts from the device"""
    return host.ansible("arista.eos.eos_facts", 'gather_subset="min"')


@pytest.fixture(scope="module", name="host_vars")
def host_vars_fixture(host):
    """Retrieve host variables from the inventory"""
    return host.ansible.get_variables()


@pytest.fixture(scope="module")
def get_host(request):
    """
    Fixture factory to retrieve host from tests that cannot use host fixture directly
    """
    inventory = request.config.getoption("ansible_inventory")

    def _get_host(hostname: str):
        host = testinfra.get_host(
            f"ansible://{hostname}?ansible_inventory={inventory}",
        )
        return host

    return _get_host


@pytest.fixture(name="avd_link")
def avd_link_fixture(avd_topology):
    """
    Fixture to test each link in the AVD topology
    """
    return avd_topology


@pytest.fixture(name="avd_p2p_link")
def avd_p2plink_fixture(avd_p2p_topology):
    """
    Fixture to test each p2p link in the AVD topology
    """
    return avd_p2p_topology


@pytest.fixture(name="vtep_intent")
def avd_vtep_fixture(avd_fabric_vtep):
    """
    Fixture to test each p2p link in the AVD topology
    """
    return avd_fabric_vtep


@pytest.fixture(scope="session", name="avd_configs")
def avd_structured_configs_fixture(request):
    """
    Load yaml data files from inventory_dir/intended/structured_configs,
    where each file represents a structured config. Returns  a dictionary
    with the file stem as the key and the value as the yaml data.
    """
    ansible_inventory = Path(request.config.getoption("ansible_inventory"))
    rootdir = Path(request.config.rootdir)

    inventory_dir = (
        ansible_inventory.parent if ansible_inventory.is_file() else ansible_inventory
    )
    return load_avd_structured_configs(inventory_dir, rootdir=Path(rootdir))


@pytest.fixture(scope="module")
def intended_config(host_vars, avd_configs):
    """Retrieve config intent from the device"""
    hostname = host_vars["inventory_hostname"]
    return avd_configs[hostname]


@pytest.fixture(scope="session", name="get_config")
def host_intent_fixture(avd_configs):
    """Get the device's intent data from"""

    def _get_host_intent(hostname: str) -> t.Optional[dict]:
        intent = avd_configs.get(hostname)
        if intent is None:
            pytest.fail(f"Could not load host intent for: {hostname}")
        return intent

    return _get_host_intent


def get_avd_fabric_loopbacks(inventory_dir: Path) -> t.Iterable[tuple]:
    """Retrieve the loopback0 address from intented configs for the fabric"""
    intent_data = load_avd_structured_configs(inventory_dir)
    return [
        (hostname, intent["loopback_interfaces"]["Loopback0"])
        for hostname, intent in intent_data.items()
        if intent.get("loopback_interfaces")
    ]


def get_avd_fabric_vteps(inventory_dir: Path) -> t.Iterable[tuple]:
    """Retrieve the VTEP address from intented configs for the fabric"""
    intent_data = load_avd_structured_configs(inventory_dir)
    vxlan_interfaces = [
        (hostname, intent["vxlan_interface"]["Vxlan1"]["vxlan"]["source_interface"])
        for hostname, intent in intent_data.items()
        if intent.get("vxlan_interface")
    ]
    return [
        (k, intent_data[k]["loopback_interfaces"][v].get("ip_address"))
        for k, v in vxlan_interfaces
    ]


class Helpers:
    """Helper functions for CLI tests."""

    @staticmethod
    @lru_cache(maxsize=120)
    def cli_command(node: testinfra.host.Host, commands: str, check_mode: bool = True):
        """Helper function to Run CLI command."""
        LOG.info("Sending commands: %s to %s", commands, node.backend.get_pytest_id())
        output = node.ansible(
            "ansible.netcommon.cli_command", f"command='{commands}'", check=check_mode
        )
        LOG.info("Output: %s", output)
        return output

    @staticmethod
    @lru_cache
    def get_interface_facts(node: testinfra.host.Host, platform: str = None):
        facts_module = FACTS_MODULES.get(platform)
        facts = node.ansible(facts_module, 'gather_subset="interfaces"')
        LOG.info("Retrieving facts for: %s", node.backend.get_pytest_id())
        LOG.info(facts)
        return facts

    @staticmethod
    @lru_cache
    def get_hostvars(node: testinfra.host.Host):
        return node.ansible.get_variables()


@pytest.fixture(scope="session")
def helpers():
    """returns a Helpers object as a fixture."""
    return Helpers


def pytest_addoption(parser):
    """
    Add options to control ansible inventory and host to test against.
    """
    parser.addoption("--fabric", action="store", help="AVD fabric")


def topo_id_func(topology: dict) -> str:
    """ID function for topology parametrization"""
    return (
        f"{topology['Node']}-{topology['Node Interface']}:"
        f"{topology['Peer Node']}-{topology['Peer Interface']}"
    )


def loopback_id_func(interface_data: tuple) -> str:
    """ID function for Lo0 intent parametrization"""
    hostname, interface = interface_data
    ip = interface.get("ip_address") if interface else "no-IP"
    return f"({hostname})-lo0-{ip}"


def pytest_generate_tests(metafunc):
    """
    Set up parametrization for the topology intent data.
    """
    ansible_inventory = metafunc.config.getoption("ansible_inventory")
    fabric_opt = metafunc.config.getoption("fabric")
    if not fabric_opt:
        pytest.fail("--fabric option is required.")

    if "avd_topology" in metafunc.fixturenames:
        link_topology = load_avd_fabric_data(
            "topology",
            inventory_dir=Path(ansible_inventory),
            rootdir=Path(metafunc.config.rootdir),
            fabric=fabric_opt,
        )
        metafunc.parametrize(
            "avd_topology", link_topology, scope="session", ids=topo_id_func
        )

    if "avd_p2p_topology" in metafunc.fixturenames:
        p2p_link_topology = load_avd_fabric_data(
            "p2p",
            inventory_dir=Path(ansible_inventory),
            rootdir=Path(metafunc.config.rootdir),
            fabric=fabric_opt,
        )
        metafunc.parametrize(
            "avd_p2p_topology",
            p2p_link_topology,
            scope="session",
            ids=topo_id_func,
        )

    if "avd_fabric_loopback" in metafunc.fixturenames:
        loopbacks = get_avd_fabric_loopbacks(Path(ansible_inventory))
        metafunc.parametrize("avd_fabric_loopback", loopbacks, ids=loopback_id_func)

    if "avd_fabric_vtep" in metafunc.fixturenames:
        vteps = get_avd_fabric_vteps(Path(ansible_inventory))
        metafunc.parametrize("avd_fabric_vtep", vteps, ids=lambda x: f"({x[0]})-vtep-{x[1]}")

    if "docker_host" in metafunc.fixturenames:
        for marker in getattr(metafunc.function, "pytestmark", []):
            if marker.name == "testinfra_hosts":
                hosts = marker.args
                metafunc.parametrize("docker_host", hosts, scope="function")

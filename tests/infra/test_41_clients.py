import pytest
import testinfra

HOSTS = [
    "docker://clab-avdirb-client1",
    "docker://clab-avdirb-client2",
    "docker://clab-avdirb-client3",
    "docker://clab-avdirb-client4",
]


@pytest.mark.parametrize(
    "client_ip",
    [
        ('10.1.10.101'),
        ('10.1.11.102'),
        ('10.1.12.103'),
        ('10.1.13.104')
    ]
)
@pytest.mark.testinfra_hosts(*(HOSTS))
def test_clients(docker_host, client_ip):
    """
    Arrange/Act: Attach to client container and test across the overlay
    Assert: The clients can ping each other
    """
    host = testinfra.get_host(docker_host)
    assert "2 packets received" in host.check_output(f'ping {client_ip} -c 1 -w 2')

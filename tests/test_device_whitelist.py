import logging
from typing import List, Tuple

import pytest

from netpalm.backend.core.security.whitelist import DeviceWhitelist, WhiteListRule

pytestmark = pytest.mark.whitelist

log = logging.getLogger(__name__)


@pytest.mark.parametrize(
    ('rule_definition', 'hostname', 'expected'),
    [
        ('*.com', 'foo.com', True),
        ('*.com', 'bar', False),
        ('foo.com', 'b.foo.com', False),
        ('*.com', '10.0.0.1', False),
        ('10.0.0.*', '10.0.0.1', True),
        ('10.0.0.0/8', '10.0.0.1', True),
        ('10.0.0.0', '10.0.0.1', False),
        ('10.0.0.1', '10.0.0.1', True)
    ]
)
def test_whitelist_rule(rule_definition: str, hostname: str, expected: bool):
    rule = WhiteListRule(rule_definition)
    assert rule.match(hostname) == expected


@pytest.mark.parametrize(('whitelist_definition', 'tests'), [
    ([], [
        ('foo.com', True),
        ('bar', True),
        ('10.0.0.1', True),
        ('172.24.1.1', True)
    ]),
    (None, [
        ('foo.com', True),
        ('bar', True),
        ('10.0.0.1', True),
        ('172.24.1.1', True)
    ]),
    ([
         "*.com"
     ], [
         ('foo.com', True),
         ('a.foo.com', True),
         ('bar', False),
         ('10.0.0.1', False),
         ('172.24.1.1', False)
     ]),
    ([
         "*.foo.com",
         "bar"
     ], [
         ('foo.com', False),
         ('a.foo.com', True),
         ('bar', True),
         ('10.0.0.1', False),
         ('172.24.1.1', False)
     ]),
    ([
         "10.0.0.0/24"
     ], [
         ('foo.com', False),
         ('a.foo.com', False),
         ('bar', False),
         ('10.0.0.1', True),
         ('172.24.1.1', False)
     ]),
])
def test_device_whitelist(whitelist_definition: List[str], tests: List[Tuple[str, bool]]):
    dwl = DeviceWhitelist(whitelist_definition)
    assert dwl.definition == whitelist_definition
    for hostname, expected in tests:
        print(f'testing {hostname} expecting {expected}')
        assert dwl.match(hostname) == expected

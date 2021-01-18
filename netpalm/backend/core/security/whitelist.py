import ipaddress
from fnmatch import fnmatch

from typing import List


class WhiteListRule:
    """
    if `definition` is a valid IPv4 or IPv6 Address or network in CIDR format, evaluate candidate
    hosts as addresses and return if they are in the equivalent network.

    else do unix filesystem-like wildcard matching ('*.foo.com' matches 'a.foo.com' but not 'foo.com' itself)
    """

    def __init__(self, definition: str):
        try:
            self.definition = ipaddress.ip_interface(definition).network
            self.type = "ip"
        except ValueError:
            self.definition = definition
            self.type = "str"

    def match(self, host: str) -> bool:
        if self.type == "ip":
            try:
                return ipaddress.ip_address(host) in self.definition
            except ValueError:
                return False

        return fnmatch(host, self.definition)


class DeviceWhitelist:
    """
    evaluate rules in order, return True if any match.  If rule list is empty, return True for anything
    """

    def __init__(self, definition: List[str]):
        self.definition = definition
        if self.definition is None:
            definition = []

        self.rules = [WhiteListRule(rule_definition) for rule_definition in definition]

    def match(self, hostname):
        if not self.rules:
            return True

        return any(rule.match(hostname) for rule in self.rules)

import ipaddress
from fnmatch import fnmatch


class WhiteListRule:
    """
    if `definition` is a valid IPv4 or IPv6 Address or network in CIDR format, evaluate candidate
    hosts as addresses and return if they are in the equivalent network.

    else do unix filesystem-like wildcard matching ('*.foo.com' matches 'a.foo.com' but not 'foo.com' itself)
    """

    def __init__(self, definition: str):
        self.type: str
        self.ip_network: ipaddress.IPv4Network | ipaddress.IPv6Network | None = None
        self.pattern: str = ""
        try:
            self.ip_network = ipaddress.ip_interface(definition).network
            self.type = "ip"
        except ValueError:
            self.pattern = definition
            self.type = "str"

    def match(self, host: str) -> bool:
        if self.type == "ip" and self.ip_network is not None:
            try:
                return ipaddress.ip_address(host) in self.ip_network
            except ValueError:
                return False

        return fnmatch(host, self.pattern)


class DeviceWhitelist:
    """
    evaluate rules in order, return True if any match.  If rule list is empty, return True for anything
    """

    def __init__(self, definition: list[str]):
        self.definition = definition
        if self.definition is None:
            definition = []

        self.rules = [WhiteListRule(rule_definition) for rule_definition in definition]

    def match(self, hostname: str) -> bool:
        if not self.rules:
            return True

        return any(rule.match(hostname) for rule in self.rules)

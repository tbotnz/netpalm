
class NetpalmError(Exception):
    """Baseclass for all netpalm errors"""
    pass


class NetpalmDriverError(NetpalmError):
    """Errors related to driver plugins"""
    pass


class NetpalmCheckError(NetpalmError):
    """Errors due to pre or post check validation failure"""
    pass


class NetpalmMetaProcessedException(NetpalmError):
    pass

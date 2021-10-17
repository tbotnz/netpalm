import logging

from netpalm.backend.core.utilities.rediz_meta import write_meta_error, write_mandatory_meta
from netpalm.backend.plugins.drivers.ncclient.ncclient_drvr import ncclien

log = logging.getLogger(__name__)


def ncclient_get(**kwargs):
    """main function for executing getconfig commands to southbound drivers"""
    lib = kwargs.get("library", False)

    result = False

    try:
        write_mandatory_meta()
        result = {}
        if lib == "ncclient":
            ncc = ncclien(**kwargs)
            sesh = ncc.connect()
            result = ncc.getmethod(sesh)
            ncc.logout(sesh)
        else:
            raise NotImplementedError(f"unknown 'library' parameter {lib}")
    except Exception as e:
        write_meta_error(f"{e}")

    return result

import sys

from netpalm import netpalm_fifo_worker, netpalm_pinned_worker


def main(args):
    worker_type = args[-1]
    if len(args) != 2 or worker_type not in ("pinned", "fifo"):
        print(
            f"Worker must be specified as either 'pinned' or 'fifo'.  e.g. `python3 worker.py pinned`"
        )
        sys.exit(1)

    if worker_type == "pinned":
        netpalm_pinned_worker.start_processworkerprocess()

    else:
        netpalm_fifo_worker.start_worker()


if __name__ == "__main__":
    main(sys.argv)
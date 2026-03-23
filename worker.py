import sys

from netpalm import netpalm_fifo_worker


def main():
    netpalm_fifo_worker.start_worker()


if __name__ == "__main__":
    main()

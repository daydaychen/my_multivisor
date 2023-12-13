import sys

from gevent import monkey

monkey.patch_thread(True)

from .server import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

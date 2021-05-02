#!/usr/bin/python3

import sys
from multiprocessing.connection import Client

ret = 0

# Connect to the status query server.
conn = Client(("localhost", 5555))
conn.send("status")
healthy = conn.recv()

# Check the status of all service backups.
for sid in healthy:
    if healthy[sid]:
        print("{}: OK".format(sid))
    else:
        print("{}: FAILED ".format(sid))
        ret = 1

conn.send("close")
conn.close()

# Exit with 1 if any of the backups has failed.
sys.exit(ret)

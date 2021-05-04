"""Query server implementation."""

from typing import Tuple
import logging
from multiprocessing.connection import Listener, Connection

from restic_docker_swarm_agent._internal.backupscheduler import BackupScheduler

logger = logging.getLogger(__name__)


class QueryServer:
    """A simple server for listening to status queries."""

    def __init__(self, listen: Tuple[str, int], scheduler: BackupScheduler):
        """Initialize the QueryServer.

        :param Tuple[str, int] listen: A tuple of the server address and port.
        :param BackupScheduler scheduler: A BackupScheduler object.
        """

        self.listen = listen
        self.scheduler = scheduler

    def handle_msg(self, listener: Listener, conn: Connection, msg) -> bool:
        """Handle a message received from a client.

        :param Listener listener: The server Listener object.
        :param conn Connection: The connection object used for communication.
        :param msg: The message received from the client.

        :return: False if the connection should be closed, True otherwise.
        :rtype: bool
        """

        client = listener.last_accepted

        if msg == "status":
            conn.send(self.scheduler.status)
        elif msg == "close":
            conn.close()
            logger.debug("Closed: %s:%s", client[0], client[1])
            return False

        return True

    def run(self) -> None:
        """Run the server."""

        logger.info(
            "Listening for status queries on %s:%s.",
            self.listen[0],
            self.listen[1]
        )
        listener = Listener(self.listen)

        while True:
            conn = listener.accept()
            client = listener.last_accepted
            logger.debug("Accepted: %s:%s", client[0], client[1])

            while True:
                msg = conn.recv()
                if not self.handle_msg(listener, conn, msg):
                    break

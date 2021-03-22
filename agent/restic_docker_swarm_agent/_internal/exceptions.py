"""Generic exception classes."""


class ResticException(Exception):
    """Exception class for restic errors."""


class RepositoryException(Exception):
    """Exception class for errors while working with repositories."""


class SwarmException(Exception):
    """Exception class for errors in managing a Docker Swarm."""


class MissingDependencyException(Exception):
    """Error class for indicating missing dependencies."""

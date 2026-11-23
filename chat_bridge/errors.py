"""Errors that every command reports the same way."""


class LocalSetupError(Exception):
    """A downloaded file, the local database, or a project file is not as expected.

    The message says what is wrong and what to do. A command prints it on one line and
    exits with code 2.
    """

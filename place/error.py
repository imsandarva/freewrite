"""A move that did not finish. title and body are what the person should read."""


class PlaceError(Exception):
    """A move that did not finish. title and body are what the person should read."""

    def __init__(self, title, body):
        super().__init__(body)
        self.title, self.body = title, body

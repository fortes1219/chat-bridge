"""The languages of the service's own texts and the sources an answer cites.

They are shared with the strategy screen, whose proposals cite the same numbered sources, so they
sit apart from the chat's request and event shapes.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel

# The languages the service writes its own texts in. A client shows the one it needs; a reader
# of the API gets both.
Language = Literal["zh-TW", "en"]
# One text in each language, keyed by language, as a localization dictionary in an API.
Localized = dict[Language, str]


class Source(BaseModel):
    """A section the answer may use, numbered as the model sees it."""

    number: int
    file: str
    title: str
    # The document's own words: what the model reads and the records keep.
    heading: str
    # The heading in each language, when it is a section name this app's sample format fixes;
    # null for any other heading, which is shown as the document wrote it.
    heading_localizations: Localized | None = None
    event_date: date | None

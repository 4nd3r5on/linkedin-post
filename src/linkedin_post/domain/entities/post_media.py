# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""Images attached to a post, checked before any browser work starts.

Limits are LinkedIn's own for the share box: at most 20 photos, 5 MB each,
and the formats its Images API accepts (JPEG, PNG, GIF).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Self

MAX_IMAGES = 20
MAX_BYTES = 5 * 1024 * 1024

_SIGNATURES = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a")


class InvalidMediaError(ValueError):
    """The images can't be posted; nothing was sent to LinkedIn."""


@dataclass(frozen=True, slots=True)
class PostMedia:
    """Absolute paths of the images to attach, in order."""

    paths: tuple[Path, ...] = ()

    @classmethod
    def parse(cls, raw: list[str] | None) -> Self:
        """Check count, path, size and format of every image.

        Raises:
            InvalidMediaError: An image is missing, too large, not JPEG/PNG/GIF,
                or there are more than 20.

        """
        raw = raw or []
        if len(raw) > MAX_IMAGES:
            msg = f"At most {MAX_IMAGES} images per post, got {len(raw)}."
            raise InvalidMediaError(msg)
        return cls(tuple(_check(entry) for entry in raw))

    def __bool__(self) -> bool:
        """Whether any image is attached."""
        return bool(self.paths)

    def __len__(self) -> int:
        """Count the images."""
        return len(self.paths)


def _check(entry: str) -> Path:
    path = Path(entry).expanduser()
    if not path.is_absolute():
        msg = f"Image path must be absolute: {entry}"
        raise InvalidMediaError(msg)
    if not path.is_file():
        msg = f"Image not found: {entry}"
        raise InvalidMediaError(msg)
    if path.stat().st_size > MAX_BYTES:
        msg = f"Image larger than 5 MB: {entry}"
        raise InvalidMediaError(msg)
    with path.open("rb") as file:
        head = file.read(8)
    if not head.startswith(_SIGNATURES):
        msg = f"Image must be JPEG, PNG or GIF: {entry}"
        raise InvalidMediaError(msg)
    return path

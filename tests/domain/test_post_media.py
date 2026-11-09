# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
from pathlib import Path

import pytest

from linkedin_post.domain.entities import InvalidMediaError, PostMedia
from linkedin_post.domain.entities.post_media import MAX_BYTES

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 16


def _write(path: Path, data: bytes) -> str:
    path.write_bytes(data)
    return str(path)


def test_none_and_empty_mean_no_media() -> None:
    assert not PostMedia.parse(None)
    assert not PostMedia.parse([])


@pytest.mark.parametrize(
    "head",
    [JPEG, b"\x89PNG\r\n\x1a\n", b"GIF89a", b"GIF87a"],
    ids=["jpeg", "png", "gif89", "gif87"],
)
def test_accepts_jpeg_png_gif(tmp_path: Path, head: bytes) -> None:
    media = PostMedia.parse([_write(tmp_path / "x", head + b"\x00" * 8)])
    assert len(media) == 1


def test_keeps_order(tmp_path: Path) -> None:
    paths = [_write(tmp_path / f"{i}.jpg", JPEG) for i in range(3)]
    assert [str(p) for p in PostMedia.parse(paths).paths] == paths


@pytest.mark.parametrize(
    ("make", "message"),
    [
        (lambda _: "relative.jpg", "absolute"),
        (lambda d: str(d / "missing.jpg"), "not found"),
        (lambda d: _write(d / "big.jpg", JPEG + b"\x00" * MAX_BYTES), "5 MB"),
        (lambda d: _write(d / "x.webp", b"RIFF\x00\x00\x00\x00WEBP"), "JPEG, PNG or GIF"),
    ],
    ids=["relative", "missing", "too-large", "webp"],
)
def test_refuses(tmp_path: Path, make, message: str) -> None:  # noqa: ANN001
    with pytest.raises(InvalidMediaError, match=message):
        PostMedia.parse([make(tmp_path)])


def test_refuses_more_than_twenty(tmp_path: Path) -> None:
    path = _write(tmp_path / "a.jpg", JPEG)
    with pytest.raises(InvalidMediaError, match="At most 20"):
        PostMedia.parse([path] * 21)

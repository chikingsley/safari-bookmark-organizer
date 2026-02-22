from __future__ import annotations

import pytest

from safari_bookmark_organizer.models import (
    WebBookmarkType,
    WebBookmarkTypeLeaf,
    WebBookmarkTypeList,
)


class TestWebBookmarkType:
    def test_hash(self) -> None:
        subject = WebBookmarkType()
        assert hash(subject) == hash(subject.web_bookmark_uuid)


class TestWebBookmarkTypeList:
    @pytest.fixture()
    def subject(self) -> WebBookmarkTypeList:
        return WebBookmarkTypeList(
            Title="Example",
            Children=[
                WebBookmarkTypeLeaf(
                    URLString="http://example.com",
                ),
            ],
        )

    def test_append(self, subject: WebBookmarkTypeList) -> None:
        new_child = WebBookmarkTypeLeaf(
            URLString="http://example.com",
        )
        subject.append(new_child)
        assert new_child == subject.children[1]

    def test_insert(self, subject: WebBookmarkTypeList) -> None:
        new_child = WebBookmarkTypeLeaf(
            URLString="http://example.com",
        )
        subject.insert(0, new_child)
        assert new_child == subject.children[0]

    def test_remove(self, subject: WebBookmarkTypeList) -> None:
        child, *_ = subject.children.copy()
        subject.remove(child)
        assert child not in subject.children

    def test_empty(self, subject: WebBookmarkTypeList) -> None:
        assert len(subject.children) != 0
        subject.empty()
        assert len(subject.children) == 0

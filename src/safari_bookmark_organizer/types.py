from __future__ import annotations

from typing import Any, Literal, NotRequired, Required, TypedDict


class BookmarkItem(TypedDict):
    title: Required[str]
    url: Required[str]
    type: NotRequired[Literal["bookmark"]]
    parent: NotRequired[str | None]
    uuid: NotRequired[str | None]


class FolderItem(TypedDict):
    title: Required[str]
    type: NotRequired[Literal["folder"]]
    parent: NotRequired[str | None]
    uuid: NotRequired[str | None]
    children: NotRequired[list[Any]]


class BookmarkNode(TypedDict):
    name: str
    url: str
    type: Literal["bookmark"]


class FolderNode(TypedDict):
    name: str
    type: Literal["folder"]
    children: list[TreeNode]


TreeNode = BookmarkNode | FolderNode


class FolderStructure(TypedDict):
    name: str
    children: list[TreeNode]


class BookmarkAnalysis(TypedDict):
    keywords: list[str]
    tags: list[str]
    confidence: float


BookmarkMove = TypedDict("BookmarkMove", {"title": str, "from": str, "to": str})


class OrganizationPlan(TypedDict):
    total_bookmarks: int
    categories: dict[str, int]
    folders_to_create: list[str]
    bookmarks_to_move: list[BookmarkMove]

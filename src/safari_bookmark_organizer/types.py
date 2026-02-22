from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class BookmarkNode(BaseModel):
    name: str
    url: str
    type: Literal["bookmark"] = "bookmark"


class FolderNode(BaseModel):
    name: str
    type: Literal["folder"] = "folder"
    children: list[TreeNode] = []


TreeNode = Annotated[
    BookmarkNode | FolderNode,
    Field(discriminator="type"),
]

FolderNode.model_rebuild()


class FolderStructure(BaseModel):
    name: str
    children: list[TreeNode] = []


FolderStructure.model_rebuild()


class BookmarkMove(BaseModel):
    title: str
    from_folder: str
    to_folder: str


class OrganizationPlan(BaseModel):
    total_bookmarks: int = 0
    categories: dict[str, int] = {}
    folders_to_create: list[str] = []
    bookmarks_to_move: list[BookmarkMove] = []

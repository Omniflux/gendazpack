from dataclasses import dataclass, field
from http.client import HTTPResponse
from pathlib import Path
from uuid import UUID

@dataclass
class AssetData:
    description: str | None = None
    content_type: str | None = None
    audience: str | None = None
    categories: list[str] = field(default_factory=list)
    compatibilities: list[str] = field(default_factory=list)
    compatibility_base: str | None = None
    tags: list[str] = field(default_factory=list)
    user_words: list[str] = field(default_factory=list)
    user_notes: str | None = None
    
@dataclass(frozen=True)
class ObjectData:
    uri: str
    scene_id: str

@dataclass
class PackageData:
    global_id: UUID | None = None
    prefix: str | None = None
    sku: int | None = None
    store: str | None = None
    name: str | None = None
    tags: list[str] = field(default_factory=list)
    artists: list[str] = field(default_factory=list)
    description: str | None = None
    image: Path | HTTPResponse | None = None
    readme: bytes | Path | None = None
    assets: dict[str, AssetData] = field(default_factory=dict)
    objects: set[ObjectData] = field(default_factory=set)
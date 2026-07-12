"""Core data model for a single person in a family tree."""

from __future__ import annotations


class Human:
    """A single person in a :class:`~familyrelations.network.Network`.

    Instances are compared and hashed by identity (the default for a plain
    ``object``), which is intentional: two people with the same name and age
    are still different people. Networkx nodes just need to be hashable, so
    this is safe to use directly as a graph node.
    """

    def __init__(self, name: str, age: int, isFemale: bool) -> None:
        self.name = name
        self.age = age
        self.isFemale = isFemale

    def __repr__(self) -> str:
        return f"Human(name={self.name!r}, age={self.age}, isFemale={self.isFemale})"

    def __str__(self) -> str:
        return self.name

"""A directed-graph backed family tree.

Edge convention
----------------
Every relation is stored as a directed edge ``(u, v, relation=R)`` meaning
"v is u's R". For example ``(alice, bob, relation="parent")`` means "bob is
alice's parent". Symmetric relations (spouse, sibling) get an edge in both
directions with the same label. Asymmetric relations (parent/child) get a
matching *inverse* edge: whenever ``(person, parent, relation="parent")`` is
added, the reverse edge ``(parent, person, relation="child")`` is added too.

This convention is what lets :meth:`Network.getParents`,
:meth:`Network.displayChildren` and :meth:`Network.displayRelation` all walk
``out_edges`` of a single node and read the label directly.
"""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Tuple

import networkx as nx

from familytree.human import Human

# (relation labels walked from person1 -> person2, in order) -> (label if
# person2 is female, label if person2 is male)
_RELATION_PATTERNS: Dict[Tuple[str, ...], Tuple[str, str]] = {
    ("parent",): ("mother", "father"),
    ("child",): ("daughter", "son"),
    ("spouse",): ("wife", "husband"),
    ("sibling",): ("sister", "brother"),
    ("parent", "parent"): ("grandmother", "grandfather"),
    ("child", "child"): ("granddaughter", "grandson"),
    ("parent", "sibling"): ("aunt", "uncle"),
    ("sibling", "child"): ("niece", "nephew"),
    ("parent", "sibling", "child"): ("cousin", "cousin"),
    # Same as above, but reachable via a shared grandparent when the sibling
    # relation itself was never explicitly recorded with addSibling().
    ("parent", "parent", "child"): ("aunt", "uncle"),
    ("parent", "child", "child"): ("niece", "nephew"),
    ("parent", "parent", "child", "child"): ("cousin", "cousin"),
    ("spouse", "parent"): ("mother-in-law", "father-in-law"),
    ("child", "spouse"): ("daughter-in-law", "son-in-law"),
    ("spouse", "sibling"): ("sister-in-law", "brother-in-law"),
    ("sibling", "spouse"): ("sister-in-law", "brother-in-law"),
}


class Network:
    def __init__(self, familyName: str) -> None:
        self.familyName = familyName
        self.root = nx.DiGraph()

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _relationExists(self, person: Human, relationship: str) -> bool:
        """Return True if `person` already has an outgoing edge of this type."""
        for _, _target, data in self.root.out_edges(person, data=True):
            if data.get("relation") == relationship:
                return True
        return False

    # ------------------------------------------------------------------
    # display
    # ------------------------------------------------------------------
    def _generationLevels(self) -> List[List[Human]]:
        """Group every person into generation levels using only parent/child
        edges (spouse and sibling edges are ignored for this purpose since
        they don't imply a generational offset)."""
        child_graph: nx.DiGraph = nx.DiGraph()
        child_graph.add_nodes_from(self.root.nodes())
        for u, v, data in self.root.edges(data=True):
            if data.get("relation") == "child":
                child_graph.add_edge(u, v)

        roots = [n for n in child_graph.nodes() if child_graph.in_degree(n) == 0]
        if not roots:
            return [list(self.root.nodes())] if self.root.nodes() else []

        depth: Dict[Human, int] = {}
        queue: deque = deque((r, 0) for r in roots)
        while queue:
            node, d = queue.popleft()
            if node in depth and depth[node] <= d:
                continue
            depth[node] = d
            for _, child in child_graph.out_edges(node):
                queue.append((child, d + 1))

        # people never reached (disconnected from any recorded parent/child
        # chain) are placed on their own level 0 so nobody is lost.
        for node in self.root.nodes():
            depth.setdefault(node, 0)

        levels: List[List[Human]] = []
        for node, d in depth.items():
            while len(levels) <= d:
                levels.append([])
            levels[d].append(node)
        return levels

    def display(self) -> None:
        """Prints the whole family tree using ASCII flow charts."""
        levels = self._generationLevels()
        if not levels:
            print(f"{self.familyName} family tree is empty.")
            return

        print(f"{self.familyName} family tree")
        for i, level in enumerate(levels):
            names = "  ".join(sorted(str(p) for p in level))
            print(f"Gen {i}: {names}")
            if i != len(levels) - 1:
                print(" " * 6 + "|")

    def displayGenerations(self, startGeneration: int, lastGeneration: int) -> None:
        """Prints the family tree from generation startGeneration to
        generation lastGeneration (inclusive) using ASCII flow charts."""
        levels = self._generationLevels()
        for i in range(startGeneration, min(lastGeneration, len(levels) - 1) + 1):
            if i < 0 or i >= len(levels):
                continue
            names = "  ".join(sorted(str(p) for p in levels[i]))
            print(f"Gen {i}: {names}")
            if i != lastGeneration:
                print(" " * 6 + "|")

    # ------------------------------------------------------------------
    # queries
    # ------------------------------------------------------------------
    def getParents(self, person: Human) -> List[Optional[Human]]:
        """return available parents of person as [mother, father]"""
        mother = None
        father = None

        for _, target, data in self.root.out_edges(person, data=True):
            if data.get("relation") == "parent":
                if target.isFemale:
                    mother = target
                else:
                    father = target

        return [mother, father]

    def displayParents(self, person: Human) -> None:
        """Prints available parents of person"""
        mother, father = self.getParents(person)
        print(f"mother: {mother}\nfather: {father}")

    def getChildren(self, person: Human) -> List[Human]:
        """return available children of person"""
        children = []
        for _, target, data in self.root.out_edges(person, data=True):
            if data.get("relation") == "child":
                children.append(target)
        return children

    def displayChildren(self, person: Human) -> None:
        """Prints available children of person"""
        children = self.getChildren(person)
        if not children:
            print(f"{person} has no recorded children.")
            return
        print(", ".join(str(c) for c in children))

    def displayRelation(self, person1: Human, person2: Human) -> None:
        """Prints how person2 is related to person1"""
        if person1 not in self.root or person2 not in self.root:
            print("One or both people are not in this family tree.")
            return

        if person1 is person2:
            print(f"{person2} is {person1} themselves.")
            return

        try:
            path = nx.shortest_path(self.root, person1, person2)
        except nx.NetworkXNoPath:
            print(f"No known relation between {person1} and {person2}.")
            return

        labels = tuple(
            self.root[path[i]][path[i + 1]]["relation"] for i in range(len(path) - 1)
        )

        pattern = _RELATION_PATTERNS.get(labels)
        if pattern is None:
            print(
                f"{person2} is related to {person1} via: {' -> '.join(labels)} "
                "(no friendly name known for this combination)."
            )
            return

        relation_name = pattern[0] if person2.isFemale else pattern[1]
        print(f"{person2} is {person1}'s {relation_name}.")

    def totalGenerations(self) -> int:
        """Returns total no of generations in tree connected to root"""
        levels = self._generationLevels()
        return len(levels)

    # ------------------------------------------------------------------
    # mutation
    # ------------------------------------------------------------------
    def addPerson(self, person: Human) -> None:
        """Adds a person with no current information of any relation. Called
        for initialisation of family tree"""
        self.root.add_node(person)

    def addRelation(
        self, person1: Human, person2: Human, relationship: str, isUnique: bool
    ) -> bool:
        """adds a relation from person1 to person2 and return True if viable"""
        if person1 not in self.root:
            self.addPerson(person1)

        if person2 not in self.root:
            self.addPerson(person2)

        if isUnique:
            if self._relationExists(person1, relationship):
                return False

            if self._relationExists(person2, relationship):
                return False

        self.root.add_edge(person1, person2, relation=relationship)
        self.root.add_edge(person2, person1, relation=relationship)

        return True

    def addSpouse(self, person: Human, spouse: Human) -> bool:
        """adds a spouse to person and return True if viable"""
        return self.addRelation(person, spouse, "spouse", True)

    def addSibling(self, person: Human, sibling: Human) -> bool:
        """adds a sibling to person and return True if viable"""
        return self.addRelation(person, sibling, "sibling", False)

    def addParent(self, person: Human, parent: Human) -> bool:
        """adds a parent to existing person and return True if viable"""
        if person not in self.root:
            self.addPerson(person)

        if parent not in self.root:
            self.addPerson(parent)

        mother, father = self.getParents(person)

        if mother and father:
            return False

        if mother and parent.isFemale:
            return False

        if father and not parent.isFemale:
            return False

        if father:
            self.root.add_edge(parent, father, relation="spouse")
            self.root.add_edge(father, parent, relation="spouse")
        if mother:
            self.root.add_edge(parent, mother, relation="spouse")
            self.root.add_edge(mother, parent, relation="spouse")

        # person's parent is `parent`; parent's child is `person`.
        self.root.add_edge(person, parent, relation="parent")
        self.root.add_edge(parent, person, relation="child")
        return True

    def addChild(self, person: Human, child: Human) -> bool:
        """adds a child to existing person and return True if viable"""
        if person not in self.root:
            self.addPerson(person)

        if child not in self.root:
            self.addPerson(child)

        # person's child is `child`; child's parent is `person`.
        self.root.add_edge(person, child, relation="child")
        self.root.add_edge(child, person, relation="parent")
        return True

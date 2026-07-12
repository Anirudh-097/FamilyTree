# FamilyTree

A small [networkx](https://networkx.org/)-backed Python library for building,
querying, and printing family trees.

## Install

```bash
pip install familytree
```

## Quick start

```python
from familytree import Human, Network

tree = Network("Stark")

ned = Human("Ned", 45, isFemale=False)
cat = Human("Catelyn", 43, isFemale=True)
robb = Human("Robb", 18, isFemale=False)
sansa = Human("Sansa", 16, isFemale=True)

tree.addSpouse(ned, cat)
tree.addChild(ned, robb)
tree.addChild(ned, sansa)
tree.addChild(cat, robb)
tree.addChild(cat, sansa)
tree.addSibling(robb, sansa)

tree.displayChildren(ned)          # -> Robb, Sansa
tree.displayRelation(robb, ned)    # -> Ned is Robb's father.
print(tree.totalGenerations())     # -> 2
tree.display()                     # ASCII generation printout
```

## Data model

Every relationship is stored as a directed edge on an internal
`networkx.DiGraph`: an edge `(u, v, relation=R)` means "`v` is `u`'s `R`".
Parent/child edges are inverses of each other and are always added as a
pair; spouse and sibling edges are symmetric and also added as a pair. This
lets most query methods simply walk `out_edges` of a single node and read
the `relation` label.

## Development

```bash
uv venv
uv pip install -e ".[dev]"
pytest
```

## License

MIT

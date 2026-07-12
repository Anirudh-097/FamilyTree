import pytest

from familyrelations import Human, Network


@pytest.fixture
def tree():
    return Network("Stark")


def test_add_person(tree):
    alice = Human("Alice", 30, True)
    tree.addPerson(alice)
    assert alice in tree.root
    assert tree.root.number_of_nodes() == 1


def test_add_parent_sets_both_directions(tree):
    child = Human("Child", 10, True)
    mother = Human("Mother", 40, True)

    assert tree.addParent(child, mother) is True
    assert tree.getParents(child) == [mother, None]
    assert tree.getChildren(mother) == [child]


def test_add_parent_rejects_two_mothers(tree):
    child = Human("Child", 10, True)
    mother = Human("Mother", 40, True)
    other_woman = Human("Other", 41, True)

    assert tree.addParent(child, mother) is True
    assert tree.addParent(child, other_woman) is False


def test_add_parent_links_spouses(tree):
    child = Human("Child", 10, True)
    father = Human("Father", 42, False)
    mother = Human("Mother", 40, True)

    assert tree.addParent(child, father) is True
    assert tree.addParent(child, mother) is True

    # adding the second parent should marry the two parents to each other
    assert tree.root[father][mother]["relation"] == "spouse"
    assert tree.root[mother][father]["relation"] == "spouse"


def test_add_child(tree):
    parent = Human("Parent", 40, False)
    child = Human("Child", 10, True)

    assert tree.addChild(parent, child) is True
    assert tree.getChildren(parent) == [child]
    assert tree.getParents(child) == [None, parent]


def test_add_sibling_not_unique(tree):
    a = Human("A", 10, True)
    b = Human("B", 12, False)
    c = Human("C", 14, False)

    assert tree.addSibling(a, b) is True
    assert tree.addSibling(a, c) is True  # multiple siblings allowed


def test_add_spouse_is_unique(tree):
    a = Human("A", 30, True)
    b = Human("B", 32, False)
    c = Human("C", 29, False)

    assert tree.addSpouse(a, b) is True
    assert tree.addSpouse(a, c) is False  # a already has a spouse
    assert tree.addSpouse(c, a) is False  # a (as person2) already has a spouse


def test_total_generations_single_person(tree):
    a = Human("A", 30, True)
    tree.addPerson(a)
    assert tree.totalGenerations() == 1


def test_total_generations_three_levels(tree):
    grandparent = Human("Grandparent", 70, False)
    parent = Human("Parent", 40, True)
    child = Human("Child", 10, False)

    tree.addChild(grandparent, parent)
    tree.addChild(parent, child)

    assert tree.totalGenerations() == 3


def test_display_children_prints(tree, capsys):
    parent = Human("Parent", 40, False)
    child = Human("Child", 10, True)
    tree.addChild(parent, child)

    tree.displayChildren(parent)
    captured = capsys.readouterr()
    assert "Child" in captured.out


def test_display_children_none(tree, capsys):
    parent = Human("Parent", 40, False)
    tree.addPerson(parent)

    tree.displayChildren(parent)
    captured = capsys.readouterr()
    assert "no recorded children" in captured.out


def test_display_relation_grandparent(tree, capsys):
    grandparent = Human("Grandparent", 70, True)
    parent = Human("Parent", 40, False)
    child = Human("Child", 10, True)

    tree.addChild(grandparent, parent)
    tree.addChild(parent, child)

    tree.displayRelation(child, grandparent)
    captured = capsys.readouterr()
    assert "grandmother" in captured.out


def test_display_relation_aunt(tree, capsys):
    grandparent = Human("Grandparent", 70, False)
    parent = Human("Parent", 40, False)
    aunt = Human("Aunt", 38, True)
    child = Human("Child", 10, True)

    tree.addChild(grandparent, parent)
    tree.addChild(grandparent, aunt)
    tree.addChild(parent, child)

    tree.displayRelation(child, aunt)
    captured = capsys.readouterr()
    assert "aunt" in captured.out


def test_display_relation_no_path(tree, capsys):
    a = Human("A", 10, True)
    b = Human("B", 12, False)
    tree.addPerson(a)
    tree.addPerson(b)

    tree.displayRelation(a, b)
    captured = capsys.readouterr()
    assert "No known relation" in captured.out

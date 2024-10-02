from __future__ import annotations
from rich import print
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, TypeVar


@dataclass
class Context:
    pass


ContextType = TypeVar("ContextType", bound=Context)


class Node(ABC):
    root_node: Node
    curr_node: Node | None = None
    """
    Base class for all nodes on the behaviour tree.
    """

    @abstractmethod
    def run(self, context: ContextType | None):
        pass


@dataclass
class NodeWrapper:
    root_node: Node
    curr_node: Node | None = None

    def run(self, context: Context):
        self.curr_node = self.root_node
        self.root_node.run(context)


class Composite(Node, ABC):
    children: tuple[Node, ...]

    def __init__(self, *children: Node):
        """
        Base class for all composite nodes.
        :param children: List of nodes to compose
        """
        super().__init__()
        self.children = children


class Sequence(Composite):
    """
    Returns false on first child failure, true if all children succeed.
    """

    def run(self, context: ContextType | None):
        # self.curr_node = self.root_node
        for child in self.children:
            if not child.run(context):
                return False
        return True


class Selector(Composite):
    """
    Returns true on first child success, false if all children fail.
    """

    def run(self, context: ContextType | None):
        # self.curr_node = self.root_node
        for child in self.children:
            if child.run(context):
                return True
        return False


def weighted_shuffle(children: list[tuple[int, Node]]) -> list[Node]:
    """
    https://softwareengineering.stackexchange.com/a/344274
    https://utopia.duth.gr/%7Epefraimi/research/data/2007EncOfAlg.pdf
    """
    order = sorted(
        range(len(children)), key=lambda i: random.random() ** (1.0 / children[i][0])
    )
    return [children[i][1] for i in order]


class RandomComposite(Node, ABC):
    children: list[tuple[int, Node]]

    def __init__(self, children: list[tuple[int, Node]] = None):
        """
        Base class for all random composite nodes.
        :param children: List of tuples containing weight and child
        """
        self.children = children or []


class RandomSelector(RandomComposite):
    """
    Returns true on first child success, false if all children fail.
    Children are shuffled prior to execution based on their weights.
    """

    def run(self, context: ContextType | None):
        for child in weighted_shuffle(self.children):
            if child.run(context):
                return True
        return False


class Decorator(Node, ABC):
    child: Node

    def __init__(self, child: Node):
        """
        Base class for all decorator nodes.
        :param child: Node to decorate
        """
        self.child = child


class Inverter(Decorator):
    """
    Inverts its child return value.
    """

    def run(self, context: ContextType | None):
        return not self.child.run(context)


class Repeater(Decorator):
    """
    Repeats action n times.
    """

    def __init__(self, child: Node, n: int = 1):
        """
        Repeats action n times.
        :param child: Node to decorate
        :param n: How many times to repeat
        """
        super().__init__(child)
        n = n

    def run(self, context: ContextType | None):
        for _ in range(self.n):
            self.child.run(context)
        return True


class Leaf(Node, ABC):
    """
    Base class for all leaf nodes.
    """

    pass


class Condition(Leaf):
    condition_func: Callable[[ContextType], bool]

    def __init__(self, condition_func: Callable[[ContextType], bool]):
        """
        Runs the given condition function.
        :param condition_func: Callable[[ContextType], bool]
        """
        self.condition_func = condition_func

    def run(self, context: ContextType | None):
        print(f"Running {self.__class__.__name__} '{repr(self.condition_func).split(" ")[1]}'")
        return self.condition_func(context)


class Action(Leaf):
    action_func: Callable[[ContextType], bool]

    def __init__(self, action_func: Callable[[ContextType], bool]):
        """
        Runs the given action function.
        :param action_func: Callable[[ContextType], bool]
        """
        self.action_func = action_func

    def run(self, context: ContextType | None):

        print(f"Running {self.__class__.__name__} '{repr(self.action_func).split(" ")[1]}'")
        return self.action_func(context)

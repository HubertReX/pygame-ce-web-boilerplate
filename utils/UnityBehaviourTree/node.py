from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum, auto
import random
from rich import print
from pydantic import BaseModel, ConfigDict, Field, PositiveInt, ValidationError
from typing import Annotated, Any, Callable, TypeVar


class NodeState(StrEnum):
    RUNNING = auto()
    SUCCESS = auto()
    FAILURE = auto()


class Node():
    # model_config = ConfigDict(extra="forbid")

    # children: list[Node] = field(default_factory=list)
    # state: NodeState = NodeState.SUCCESS
    # # Annotated[NodeState, Field(NodeState.SUCCESS, description="node state")]
    # context: dict[str, Any] =  field(default_factory=dict)
    # # Annotated[dict[str, Any], Field(default_factory=dict, description="context data")]
    # parent: Optional[Node] = None
    # Annotated[Node, Field(default_factory=list, description="node's children")]

    def __init__(self, *children: Node) -> None:
        super().__init__()
        self.context: dict[str, Any] = {}
        self.children: list[Node] = []
        self.parent: Node | None = None
        self.state: NodeState = NodeState.SUCCESS

        for child in children:
            self._attach(child)

    def get_id(self) -> int:
        if self.parent:
            if self.parent.children:
                id = self.parent.children.index(self) + 1
            else:
                id = 1
        else:
            id = 1

        return id

    def get_suffix(self) -> str:
        return f"_{self.get_id():02}"

    def get_node_children(self, indent: int = 0) -> list[str]:
        res: list[str] = []
        res.append(
            f"{"    " * indent}[bright_magenta]{self.__class__.__name__}{self.get_suffix()}"
            "[/][bright_white]([/]"
        )
        if self.children:
            for child in self.children:
                res += child.get_node_children(indent + 1)
            res.append(f"{"    " * indent}[bright_white])[/]")
        return res

    def get_tree(self, indent: int = 0) -> list[tuple[int, str, int, str]]:
        res: list[tuple[int, str, int, str]] = []
        res.append((indent, self.__class__.__name__, self.get_id(), ""))
        if self.children:
            for child in self.children:
                res += child.get_tree(indent + 1)
        return res

    def format2str(self, node: tuple[int, str, int, str]) -> str:
        res: list[str] = [f"{"     " * node[0]}[bright_magenta]{node[1]}_{node[2]:02}[/]",
                          f"[bright_white]([/][green]{node[3]}[/][bright_white])[/]",
                          ]

        return "".join(res)

    def format2json(self, node: tuple[int, str, int, str]) -> str:
        res: list[str] = [f"{"     " * node[0]}'{node[1]}' : ["]
        if node[3]:
            res.append(f" '{node[3]}' ]")

        return "".join(res)

    def format2mm(self, node: tuple[int, str, int, str]) -> str:
        res: list[str] = []
        if node[1].beginswith("Condition"):
            res.append(f"    {node[1]}_{node[2]:02}([\"{node[3]}\"])")
        elif node[1].beginswith("Action"):
            res.append(f"    {node[1]}_{node[2]:02}([\"{node[3]}\"])")
        return res

    def print_tree(self) -> None:
        tree = self.get_tree()
        for leaf in tree:
            print(self.format2str(leaf))

    def print_json(self) -> None:
        tree = self.get_tree()
        indent = 0  # tree[1][0]

        for leaf in tree:
            if leaf[0] < indent:
                print(f"{"     " * leaf[0]}]")
            print(self.format2json(leaf), leaf[0], indent)
            # print(leaf[0], indent)
            indent = leaf[0]
        print("]")

    def __repr__(self) -> str:
        rows = self.get_node_children()

        return f"{"\n".join(rows)}"

    def _attach(self, node: Node) -> None:
        node.parent = self
        # node.context = self.context
        self.children.append(node)

    def evaluate(self) -> NodeState:
        result = NodeState.SUCCESS
        evaluate_trace(self, result)
        return result

    def has_context(self, key: str) -> bool:
        return key in self.context

    def get_context(self, key: str, default: str | int | float = "") -> Any | str:
        if not self.has_context(key):
            # if self.parent:
            #     if self.parent.has_context(key):
            #         self.set_context(key, self.parent.get_context(key))
            #     else:
            #         self.set_context(key, default)
            # else:
            self.set_context(key, default)
        return self.context.get(key, default)

    def setup_context(self, context: dict[str, Any]) -> None:
        self.context = context
        for child in self.children:
            if "traceback" not in child.context:
                child.setup_context(context)

    def set_context(self, key: str, value: Any) -> None:
        self.context[key] = value

    def del_context(self, key: str) -> None:
        del self.context[key]


@dataclass
class BehaviorTreeBase():
    # model_config = ConfigDict(extra="forbid")

    _root: Node | None = None
    # Annotated[Node, Field(default_factory=Node, description="root node of the behavior tree")]

    def __post_init__(self) -> None:
        self.setup()
        if self._root:
            # self._root.set_context("traceback", ["ROOT"])
            self._root.setup_context({"traceback": ["ROOT"]})
            self._root.print_tree()
            self._root.print_json()

    def setup(self) -> None:
        return

    def update(self, dt: float) -> None:
        if self._root:
            self._root.set_context("dt", dt)
            time_elapsed = self._root.get_context("time_elapsed", 0.0)
            self._root.set_context("time_elapsed", time_elapsed + dt)
            self._root.evaluate()


class Selector(Node):

    def evaluate(self) -> NodeState:
        traceback = self.get_context("traceback", [])
        traceback.append(f"{self.__class__.__name__}{self.get_suffix()}")

        for child in self.children:
            result = child.evaluate()
            match result:
                case NodeState.FAILURE:
                    continue
                case NodeState.RUNNING:
                    # evaluate_trace(self, result)
                    traceback.pop()
                    return result
                case NodeState.SUCCESS:
                    # evaluate_trace(self, result)
                    traceback.pop()
                    return result
                case _:
                    continue

        result = NodeState.FAILURE
        # evaluate_trace(self, result)
        traceback.pop()
        return result


class Sequence(Node):

    def evaluate(self) -> NodeState:
        traceback = self.get_context("traceback", [])
        traceback.append(f"{self.__class__.__name__}{self.get_suffix()}")

        any_child_running = False
        for child in self.children:
            result = child.evaluate()
            match result:
                case NodeState.FAILURE:
                    # evaluate_trace(self, result)
                    traceback.pop()
                    return result
                case NodeState.RUNNING:
                    any_child_running = True
                    continue
                case NodeState.SUCCESS:
                    continue
                case _:
                    result = NodeState.SUCCESS
                    # evaluate_trace(self, result)
                    traceback.pop()
                    return result

        result = NodeState.RUNNING if any_child_running else NodeState.SUCCESS
        # evaluate_trace(self, result)
        traceback.pop()
        return result


@dataclass
class Context:
    pass


def dummy(node: Node) -> bool:
    return False


ContextType = TypeVar("ContextType", bound=Context)


# class ConditionOld(Node):
#     condition_func: Callable[[ContextType], bool]

#     def __init__(self, condition_func: Callable[[ContextType], bool]):
#         """
#         Runs the given condition function.
#         :param condition_func: Callable[[ContextType], bool]
#         """
#         self.condition_func = condition_func

#     def evaluate(self, context: ContextType | None):
#         print(f"Running {self.__class__.__name__} '{repr(self.condition_func).split(" ")[1]}'")
#         return self.condition_func(context)


class Condition(Node):
    # def __repr__(self) -> str:
    #     # children = [f"    {child}" for child in self.children]
    #     return f"    {self.__class__.__name__}.{repr(self.condition_func).split(" ")[1]}()"

    def get_node_children(self, indent: int = 0) -> list[str]:
        res: list[str] = []
        res.append(f"{"    " * indent}[bright_magenta]{self.__class__.__name__}[/][bright_white]([/]"
                   f"[green]{repr(self.condition_func).split(" ")[1]}[/][bright_white])[/]"
                   )
        return res

    def get_tree(self, indent: int = 0) -> list[tuple[int, str, int, str]]:
        res: list[tuple[int, str, int, str]] = []
        res.append((indent, self.__class__.__name__, self.get_id(), repr(self.condition_func).split(" ")[1]))

        return res

    def __init__(self, condition_func: Callable[[Node], bool]) -> None:
        """
        Runs the given condition function.
        :param condition_func: Callable[[Node], bool]
        """
        # super().__init__()
        self.condition_func: Callable[[Node], bool] = condition_func
        # self.condition_func = condition_func
        self.children: list[Node]  = []
        self.context: dict[str, Any] = {}
        self.state: NodeState = NodeState.SUCCESS
        self.parent: Node | None = None
        # if self.parent:
        #     self.context = self.parent.context

    def evaluate(self) -> NodeState:
        # print(f"Running {self.__class__.__name__} '{repr(self.condition_func).split(" ")[1]}'")
        traceback = self.get_context("traceback", [])
        traceback.append(self.__class__.__name__)
        traceback.append(repr(self.condition_func).split(" ")[1])

        result = NodeState.SUCCESS if self.condition_func(self) else NodeState.FAILURE
        evaluate_trace(self, result)
        traceback.pop()
        traceback.pop()
        return result


class Action(Node):
    # def __repr__(self) -> str:
    #     # children = [f"    {child}" for child in self.children]
    #     return f"    {self.__class__.__name__}.{repr(self.action_func).split(" ")[1]}()"

    def get_node_children(self, indent: int = 0) -> list[str]:
        res: list[str] = []
        res.append(f"{"    " * indent}[bright_magenta]{self.__class__.__name__}[/][bright_white]([/]"
                   f"[green]{repr(self.action_func).split(" ")[1]}[/][bright_white])[/]"
                   )

    def get_tree(self, indent: int = 0) -> list[tuple[int, str, int, str]]:
        res: list[tuple[int, str, int, str]] = []
        res.append((indent, self.__class__.__name__, self.get_id(), repr(self.action_func).split(" ")[1]))

        return res

    def __init__(self, action_func: Callable[[Node], bool]) -> None:
        """
        Runs the given action function.
        :param action_func: Callable[[Node], bool]
        """
        # super().__init__()
        self.action_func = action_func
        self.children: list[Node]  = []
        self.context: dict[str, Any] = {}
        self.state: NodeState = NodeState.SUCCESS
        self.parent: Node | None = None
        # if self.parent:
        #     self.context = self.parent.context

    def evaluate(self) -> NodeState:
        traceback = self.get_context("traceback", [])
        traceback.append(self.__class__.__name__)
        traceback.append(repr(self.action_func).split(" ")[1])
        # print(f"Running {self.__class__.__name__} '{repr(self.action_func).split(" ")[1]}'")
        result = NodeState.SUCCESS if self.action_func(self) else NodeState.RUNNING
        evaluate_trace(self, result)
        traceback.pop()
        traceback.pop()
        return result


def ns2str(state: NodeState) -> str:
    match state:
        case NodeState.SUCCESS:
            return "[bright_green]SUCCESS[/]"
        case NodeState.RUNNING:
            return "[bright_yellow]RUNNING[/]"
        case NodeState.FAILURE:
            return "[bright_red]FAILURE[/]"
    return ""


def evaluate_trace(node: Node, node_result: NodeState):
    traceback = node.get_context("traceback", [f"!{node.__class__.__name__}!"])
    SHOW_CONTEXT = True
    if SHOW_CONTEXT:
        context = {key: val for key, val in node.context.items() if key not in ["traceback", "time_elapsed", "dt"]}
    else:
        context = {}
    print(f"{context} [bright_magenta]{"[/][bright_white].[/][bright_magenta]".join(traceback[:-1])}[/]"
          f"('{traceback[-1]}') => {ns2str(node_result)}")  # [{len(node.children)}]


# def stats(node: Node) -> str:
#     return f"{node.__class__.__name__}({len(node.children)})"


def is_healthy(node: Node) -> bool:
    res = True  # random.randint(0, 2) == 0
    # print(f"'is_healthy' {res}")

    return res


def is_enemy_in_attack_range(node: Node) -> bool:
    res = random.randint(0, 2) == 0
    # print(f"'is_enemy_in_attack_range' {res}")

    return res


def is_enemy_in_FOV_range(node: Node) -> bool:
    res = random.randint(0, 2) == 0
    return res


def approach_enemy(node: Node) -> bool:
    return True


def is_tired(node: Node) -> bool:
    tiredness = node.get_context("tiredness", 0)
    time_to_rest = node.get_context("time_to_rest", 0)
    if tiredness >= 15:
        if time_to_rest == 0:
            node.set_context("time_to_rest", 3)
        result = True
    else:
        result = False
    # print(f"'is_tired' {tiredness}")
    return result


def rest(node: Node) -> bool:
    time_to_rest = node.get_context("time_to_rest", 0)
    time_to_rest -= 1
    if time_to_rest <= 0:
        node.set_context("tiredness", 0)
        node.set_context("time_to_rest", 0)
        result = True
    else:
        node.set_context("time_to_rest", time_to_rest)
        result = False
    # print(f"'is_tired' {tiredness}")
    return result


def patrol_area(node: Node) -> bool:
    tiredness = node.get_context("tiredness", 0)
    node.set_context("tiredness", tiredness + 10)

    res = False  # random.randint(0, 2) == 0
    return res


def attack(node: Node) -> bool:
    res = True  # random.randint(0, 2) == 0
    # print("'attack'")

    return res


def wander(node: Node) -> bool:
    res = False  # random.randint(0, 2) == 0
    # print("'wandering...'")

    return res


class PatrolBehaviorTree(BehaviorTreeBase):

    def setup(self) -> Node:

        # check_in_range.setup_context({"traceback": ["check_in_range"]})
        # check_in_range.set_context("traceback", ["check_in_range"])
        self._root = Selector(
            Sequence(
                Condition(is_tired),
                Action(rest),
            ),
            Sequence(
                Selector(Condition(is_enemy_in_attack_range),
                         Action(wander)),
                Action(attack),
            ),
            Sequence(
                Condition(is_enemy_in_FOV_range),
                Action(approach_enemy),
            ),
            Action(patrol_area)
        )
        # self._root.setup_context({"traceback": ["ROOT"]})


def main() -> None:
    ai = PatrolBehaviorTree()

    DURATION = 1.0
    loop_count = 0.0

    while loop_count < DURATION:
        loop_count += 1.0
        print(f"[cyan]loop[/] {loop_count:4.1f} [cyan]###########################################################")
        ai.update(1.0)


if __name__ == "__main__":
    main()

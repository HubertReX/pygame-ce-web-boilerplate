from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum, auto

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
        # self.state: NodeState = NodeState.SUCCESS

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
        context = {key: val for key, val in node.context.items(
        ) if key not in ["traceback", "time_elapsed", "dt", "inventer"]}
    else:
        context = {}
    print(f"{context} [bright_magenta]{"[/][bright_white].[/][bright_magenta]".join(traceback[:-1])}[/]"
          f"('{traceback[-1]}') => {ns2str(node_result)}")  # [{len(node.children)}]

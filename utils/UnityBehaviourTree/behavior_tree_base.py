from node import Node, NodeState, evaluate_trace
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class BehaviorTreeBase():
    _root: Node | None = None

    def __post_init__(self) -> None:
        self.setup()
        if self._root:
            self._root.setup_context({"traceback": ["ROOT"]})
            # self._root.print_tree()
            # self._root.print_json()

    def setup(self) -> None:
        return

    def update(self, dt: float) -> None:
        if self._root:
            self._root.set_context("dt", dt)
            time_elapsed = self._root.get_context("time_elapsed", 0.0)
            self._root.set_context("time_elapsed", time_elapsed + dt)
            self._root.evaluate()

#############################################################################################################


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

#############################################################################################################


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

#############################################################################################################


class Condition(Node):

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
        self.condition_func: Callable[[Node], bool] = condition_func
        self.children: list[Node]  = []
        self.context: dict[str, Any] = {}
        self.state: NodeState = NodeState.SUCCESS
        self.parent: Node | None = None

    def evaluate(self) -> NodeState:
        traceback = self.get_context("traceback", [])
        traceback.append(self.__class__.__name__)
        traceback.append(repr(self.condition_func).split(" ")[1])

        result = NodeState.SUCCESS if self.condition_func(self) else NodeState.FAILURE
        evaluate_trace(self, result)
        traceback.pop()
        traceback.pop()
        return result

#############################################################################################################


class Action(Node):

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
        self.action_func = action_func
        self.children: list[Node]  = []
        self.context: dict[str, Any] = {}
        self.state: NodeState = NodeState.SUCCESS
        self.parent: Node | None = None

    def evaluate(self) -> NodeState:
        traceback = self.get_context("traceback", [])
        traceback.append(self.__class__.__name__)
        traceback.append(repr(self.action_func).split(" ")[1])
        result = NodeState.SUCCESS if self.action_func(self) else NodeState.RUNNING
        evaluate_trace(self, result)
        traceback.pop()
        traceback.pop()
        return result

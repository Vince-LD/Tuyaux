from concurrent.futures import Future, ThreadPoolExecutor, wait
from enum import Enum, IntFlag, auto, Flag

from functools import reduce
from itertools import repeat
import time
from typing import Callable, Iterable, Optional, Self
from src.exceptions import CommandFailed, PipelineError
from src.steps.base_step import RootStep
from steps import BaseStep, PipelineContext
from steps import TestStep
import logging
from threading import Lock
import graphviz

logging.basicConfig(level=logging.DEBUG)


class NodeStatus(Flag):
    UNKNOWN = auto()
    RUNNING = auto()
    FINISHED = auto()
    SKIPPED = auto()
    ERROR = auto()

NODE_PASSED = NodeStatus.FINISHED | NodeStatus.ERROR

class PipeNode:
    def __init__(self, name="") -> None:
        self.name = name
        self.steps: list[BaseStep] = []
        self.parent_nodes: set[PipeNode] = set()
        self.child_nodes: set[PipeNode] = set()
        self._status = NodeStatus.UNKNOWN
        self._error: Optional[BaseException] = None

    def run(self, ctx: PipelineContext):
        logging.info(
            f"{", ".join([n.name+ ":" + str(n.status) for n in self.parent_nodes])} => {self.name}"
        )
        if not self._all_previous_finished():
            logging.info(
                f"{self.name} cannot run yet, "
                f"{", ".join([n.name+ ":" + str(n.status) for n in self.parent_nodes])}"
            )
            return
        try:
            for step in self.steps:
                step.run(ctx)
        except BaseException as e:
            self._error = e
            self._status = NodeStatus.ERROR
            return
        self._status = NodeStatus.FINISHED

    def add_step(self, step: BaseStep):
        self.steps.append(step)

    def add_children_node(self, node: Self):
        self.child_nodes.add(node)

    def add_parent_node(self, node: Self):
        self.parent_nodes.add(node)

    def __str__(self) -> str:
        return f"{' -> '.join([step.__class__.__name__ for step in self.steps])}"

    def _all_previous_finished(self) -> bool:
        return reduce(
            lambda bool_, node: bool_ and bool(node.status & NODE_PASSED),
            self.parent_nodes,
            True,
        )
    
    @property
    def first_step(self):
        return self.steps[0]
    
    @property
    def last_step(self):
        return self.steps[-1]

    @property
    def status(self) -> NodeStatus:
        return self._status

    @property
    def error(self) -> Optional[BaseException]:
        return self._error

    def preview(self, graph: graphviz.Digraph) -> graphviz.Digraph:
        sg = graphviz.Digraph(f"cluster_{self.name}")
        if self.steps:
            for prev_id, step in enumerate(self.steps[1:]):
                sg.edge(self.steps[prev_id].name, step.name)
        sg.attr(label=self.name)
        graph.subgraph(sg)
        return graph

class Pipeline:
    def __init__(self, root_node: Optional[PipeNode] = None) -> None:
        self.root_node = root_node or PipeNode("Pipeline root")
        self.last_node = PipeNode("Pipeline end")
        self.nodes: list[PipeNode] = []
        self._lock = Lock()
        self._remaining_nodes: int = 0
        self._running_nodes: int = 0
        self.runtime_error: Optional[BaseException] = None

    def add_children_to(self, parent_node: PipeNode, child_nodes: Iterable[PipeNode]):
        for node in child_nodes:
            parent_node.add_children_node(node)
            node.add_parent_node(parent_node)
            self.nodes.append(node)

    def add_parents_to(self, parent_nodes: Iterable[PipeNode], into_node: PipeNode):
        for node in parent_nodes:
            node.add_children_node(into_node)
            into_node.add_parent_node(node)
            self.nodes.append(into_node)

    def execute(self, ctx: PipelineContext):
        self.remaining_nodes = len(self.nodes)
        self.running_nodes = 0
        with ThreadPoolExecutor(max_workers=ctx.thread_count) as executor:
            self._parse_run(ctx, self.root_node, executor)
            while self._keep_running():
                time.sleep(1)
        if self.runtime_error is not None:
            logging.exception(self.runtime_error)

    def _parse_run(
        self, ctx: PipelineContext, node: PipeNode, executor: ThreadPoolExecutor
    ):
        if node.status is not NodeStatus.UNKNOWN:
            return
        
        node.run(ctx)
        self.remaining_nodes -= 1
        
        if node.status is NodeStatus.ERROR:
            self.runtime_error = node.error
            return 
        
        executor.map(self._parse_run, repeat(ctx), node.child_nodes, repeat(executor))

    @property
    def remaining_nodes(self) -> int:
        with self._lock:
            return self._remaining_nodes

    @remaining_nodes.setter
    def remaining_nodes(self, value: int):
        with self._lock:
            self._remaining_nodes = value

    # @property
    # def running_nodes(self) -> int:
    #     with self._lock:
    #         return self._running_nodes

    # @running_nodes.setter
    # def running_nodes(self, value: int):
    #     with self._lock:
    #         self._running_nodes = value

    def _keep_running(self):
        return (
            self.remaining_nodes > 0
            and self.runtime_error is None
            # and self.running_nodes > 0
        )

    def build(self):
        pass

    def preview(self) -> graphviz.Digraph:
        graph = graphviz.Digraph("Pipeline", filename="./test.svg", strict=True)
        graph.attr(compound='true')
        if not self.root_node.steps:
            self.root_node.add_step(RootStep())
        self._preview(self.root_node, graph)
        self._link(self.root_node, graph)
        return graph
    
    def _preview(self, node: PipeNode, graph: graphviz.Digraph):
        node.preview(graph)
        for child_node in node.child_nodes:
            self._preview(child_node, graph)

    def _link(self, node: PipeNode, graph: graphviz.Digraph):
        for child_node in node.child_nodes:
            graph.edge(f"{node.last_step.name}", f"{child_node.first_step.name}", ltail=node.name, lhead=child_node.name)
            self._link(child_node, graph)


class Step1(TestStep):
    NAME = "1st step"


class Step2(TestStep):
    NAME = "2nd step"
    def run(self, ctx: PipelineContext):
        super().run(ctx)
        print("ERROR SHOULD BE RAISED")
        raise CommandFailed("FAILED", 1)


class Step3(TestStep):
    NAME = "3rd step"


class Step4(TestStep):
    NAME = "4th step"


class Step5(TestStep):
    NAME = "5th step"


class Step6(TestStep):
    NAME = "6th step"


class Step7(TestStep):
    NAME = "7th step"


class Step8(TestStep):
    NAME = "8th step"


class Step9(TestStep):
    NAME = "9th step"


class Step10(TestStep):
    NAME = "10th step"


class Step11(TestStep):
    NAME = "10th step"


if __name__ == "__main__":
    pipeline = Pipeline()

    node0 = pipeline.root_node

    node1 = PipeNode("Node 1")
    node1.add_step(Step1("A"))
    node1.add_step(Step2("B"))

    node2 = PipeNode("Node 2")
    node2.add_step(Step2("C"))
    node2.add_step(Step2("D"))

    node3 = PipeNode("Node 3")
    node3.add_step(Step3("E"))
    node3.add_step(Step3("F"))

    node4 = PipeNode("Node 4")
    node4.add_step(Step4("G"))
    node4.add_step(Step4("H"))

    node5 = PipeNode("Node 5")
    node5.add_step(Step5("I"))
    node5.add_step(Step5("J"))

    pipeline.add_children_to(node0, (node1, node2))
    pipeline.add_children_to(node2, (node3, node4))
    pipeline.add_parents_to((node1, node3, node4), node5)

    # pipeline.execute(PipelineContext())

    g = pipeline.preview()
    g.view()
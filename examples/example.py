import os
from tuyau.pipeline import Pipeline, PipeNode
from example_utils import (
    ExampleContext,
    AdditionStep,
    MutliplyStep,
    LogStep,
    SkipStep,
)
from tuyau.context import CtxVar


def main():
    pipeline = Pipeline(ExampleContext, "Example Pipeline")

    context = ExampleContext(
        input_x=CtxVar(1.5),
        input_y=CtxVar(8),
    )

    node1 = PipeNode("Process node 1").add_steps(
        AdditionStep(
            a_field=context.input_x,
            b_field=context.input_y,
            res_field=context.result_step1,
            name="Step 1.1",
        ),
        LogStep(context.result_step1, name="Step 1.2"),
        MutliplyStep(
            a_field=context.result_step1,
            b_field=context.result_step1,
            res_field=context.result_step1,
            name="Step 1.3",
            comment="Square previous result",
        ),
        LogStep(context.result_step1, name="Step 1.2"),
    )

    node2 = PipeNode("Process node 2").add_steps(SkipStep("Skip step 2"))

    node3 = PipeNode(name="Process node 3").add_steps(
        AdditionStep(
            a_field=context.input_x,
            b_field=context.input_y,
            res_field=context.result_step3,
            name="Step 3.1",
        )
    )

    node4 = PipeNode("Process node 4").add_steps(
        MutliplyStep(
            a_field=context.input_x,
            b_field=context.input_x,
            res_field=context.result_step4,
            name="Step 4.1",
        )
    )

    node5 = PipeNode("Process node 5").add_steps(
        AdditionStep(
            a_field=context.result_step3,
            b_field=context.result_step4,
            res_field=context.result_step5,
            name="Step 5.1",
        )
    )

    node6 = PipeNode("Process node 6").add_steps(
        MutliplyStep(
            a_field=context.result_step3,
            b_field=context.result_step5,
            res_field=context.result_step6,
            name="Step 6.1"
        ),
        LogStep(context.result_step6, name=""),
    )

    (
        pipeline.add_children_to(pipeline.root_node, node1, node2)
        .add_children_to(node2, node3, node4)
        .add_parents_to(node5, node3, node4)
        .add_parents_to(node6, node5, node1)
        .connect_final_node()
    )

    directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

    # graph = pipeline.graph(preview=True)
    # graph.render("example_preview", directory=directory, format="svg")
    # graph.render("example_preview", directory=directory, format="png")

    pipeline.execute(context)
    graph = pipeline.graph()
    graph.render("example", directory=directory, format="svg")
    graph.render("example", directory=directory, format="png")


if __name__ == "__main__":
    main()

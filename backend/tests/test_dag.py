import pytest
from app.models.task import MicroAction, TaskDAG, TaskStatus, CognitiveLoad
from app.core.logic import DAGManager, PacingEngine, CommandGenerator
from app.models.session import PacingMode

@pytest.fixture
def simple_dag():
    nodes = {
        "a": MicroAction(id="a", title="A", description="Step A", estimated_minutes=5, cognitive_load=CognitiveLoad.LOW, dependencies=[]),
        "b": MicroAction(id="b", title="B", description="Step B", estimated_minutes=5, cognitive_load=CognitiveLoad.LOW, dependencies=["a"]),
        "c": MicroAction(id="c", title="C", description="Step C", estimated_minutes=5, cognitive_load=CognitiveLoad.LOW, dependencies=["a"]),
    }
    return TaskDAG(id="dag-1", goal="Simple", nodes=nodes, entry_nodes=["a"])


def test_get_available_tasks_initial(simple_dag):
    mgr = DAGManager(simple_dag)
    avail = mgr.get_available_tasks()
    assert len(avail) == 1
    assert avail[0].id == "a"


def test_complete_and_advance(simple_dag):
    mgr = DAGManager(simple_dag)
    mgr.mark_completed("a")
    avail = mgr.get_available_tasks()
    assert {t.id for t in avail} == {"b", "c"}


def test_goal_reached(simple_dag):
    mgr = DAGManager(simple_dag)
    assert not mgr.is_goal_reached()
    mgr.mark_completed("a")
    mgr.mark_completed("b")
    mgr.mark_completed("c")
    assert mgr.is_goal_reached()


def test_topological_order(simple_dag):
    mgr = DAGManager(simple_dag)
    order = mgr.topological_order()
    assert order.index("a") < order.index("b")
    assert order.index("a") < order.index("c")


def test_cycle_detection():
    nodes = {
        "a": MicroAction(id="a", title="A", description="Step A", estimated_minutes=5, cognitive_load=CognitiveLoad.LOW, dependencies=["b"]),
        "b": MicroAction(id="b", title="B", description="Step B", estimated_minutes=5, cognitive_load=CognitiveLoad.LOW, dependencies=["a"]),
    }
    dag = TaskDAG(id="dag-cycle", goal="Cycle", nodes=nodes, entry_nodes=["a"])
    mgr = DAGManager(dag)
    with pytest.raises(ValueError, match="Cycle detected"):
        mgr.topological_order()


def test_next_step_prefers_low_load_when_overwhelmed(simple_dag):
    mgr = DAGManager(simple_dag)
    mgr.mark_completed("a")
    step = mgr.get_next_step(PacingMode.OVERWHELMED)
    assert step is not None
    assert step.cognitive_load == CognitiveLoad.LOW


def test_pacing_engine_overwhelmed():
    task = MicroAction(id="x", title="X", description="X", estimated_minutes=8, cognitive_load=CognitiveLoad.HIGH, dependencies=[])
    adjusted = PacingEngine.adjust_task(task, PacingMode.OVERWHELMED)
    assert adjusted.estimated_minutes == 5
    assert adjusted.cognitive_load == CognitiveLoad.LOW


def test_pacing_engine_focus():
    task = MicroAction(id="x", title="X", description="X", estimated_minutes=8, cognitive_load=CognitiveLoad.HIGH, dependencies=[])
    adjusted = PacingEngine.adjust_task(task, PacingMode.IN_FOCUS)
    assert adjusted.estimated_minutes == 8
    assert adjusted.cognitive_load == CognitiveLoad.HIGH


def test_command_generator_with_command():
    step = MicroAction(id="a", title="A", description="Run", estimated_minutes=5, cognitive_load=CognitiveLoad.LOW, command="pytest", file_operations=["/tmp/x"])
    cmds = CommandGenerator.generate_for_step(step)
    assert len(cmds) == 1
    assert cmds[0]["command"] == "pytest"
    assert "/tmp/x" in cmds[0]["creates_files"]


def test_command_generator_without_command():
    step = MicroAction(id="a", title="A", description="Manual", estimated_minutes=5, cognitive_load=CognitiveLoad.LOW, dependencies=[])
    cmds = CommandGenerator.generate_for_step(step)
    assert len(cmds) == 1
    assert "echo" in cmds[0]["command"]

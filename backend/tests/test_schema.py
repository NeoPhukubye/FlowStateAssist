from app.models.task import MicroAction, TaskDAG, TaskStatus, CognitiveLoad

dag_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "goal": {"type": "string"},
        "nodes": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "estimated_minutes": {"type": "integer", "minimum": 1, "maximum": 10},
                        "cognitive_load": {"type": "string", "enum": ["low", "medium", "high"]},
                        "command": {"type": "string"},
                        "dependencies": {"type": "array", "items": {"type": "string"}},
                        "file_operations": {"type": "array", "items": {"type": "string"}},
                        "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "blocked"]},
                    },
                    "required": ["id", "title", "description", "estimated_minutes", "cognitive_load", "dependencies"],
                }
            },
        },
        "entry_nodes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["id", "goal", "nodes", "entry_nodes"],
}


def test_micro_action_schema():
    node = MicroAction(
        id="a", title="A", description="desc", estimated_minutes=5,
        cognitive_load=CognitiveLoad.LOW, command="echo hi", dependencies=[], file_operations=["/tmp/a"]
    )
    assert node.estimated_minutes == 5
    assert node.status == TaskStatus.PENDING


def test_dag_schema_validation():
    import json
    from jsonschema import validate, ValidationError
    sample = {
        "id": "dag-1",
        "goal": "Test",
        "nodes": {
            "a": {
                "id": "a", "title": "A", "description": "desc", "estimated_minutes": 5,
                "cognitive_load": "low", "command": "echo hi", "dependencies": [], "file_operations": []
            }
        },
        "entry_nodes": ["a"],
    }
    validate(instance=sample, schema=dag_schema)
    sample["nodes"]["a"]["estimated_minutes"] = 20
    try:
        validate(instance=sample, schema=dag_schema)
    except ValidationError:
        pass
    else:
        raise AssertionError("Schema validation failed to catch out-of-range minutes")

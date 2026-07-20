"""Smoke test for the Locust files.

Locust's gevent monkey-patch is incompatible with pytest-django's
database setup (it triggers a ``RecursionError`` in urllib3). We
sidestep the import by parsing the source for class definitions and
``@task`` decorations. The real load test still runs with
``locust -f ops/locust/locustfile.py`` against a live stack.
"""

import ast
from pathlib import Path


def _locust_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "locust"


def _parse(path: Path) -> ast.Module:
    """Parse a Python source file as an AST."""
    return ast.parse(path.read_text())


def _class_with_tasks(path: Path, class_name: str) -> tuple[ast.ClassDef, int]:
    """Return ``(class_def, task_count)`` for ``class_name`` in ``path``."""
    tree = _parse(path)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            tasks = [
                m
                for m in node.body
                if isinstance(m, ast.FunctionDef)
                and any(
                    (isinstance(d, ast.Name) and d.id == "task")
                    or (
                        isinstance(d, ast.Call)
                        and isinstance(d.func, ast.Name)
                        and d.func.id == "task"
                    )
                    for d in m.decorator_list
                )
            ]
            return node, len(tasks)
    raise AssertionError(f"{class_name} not found in {path}")


def test_admin_user_has_at_least_one_task():
    """``AdminUser`` is a Locust HttpUser with >= 1 ``@task`` method."""
    admin_path = _locust_dir() / "users_admin.py"
    cls, tasks = _class_with_tasks(admin_path, "AdminUser")
    bases = [b.id for b in cls.bases if isinstance(b, ast.Name)]
    assert "HttpUser" in bases
    assert tasks >= 1


def test_ai_user_has_at_least_one_task():
    """``AiUser`` is a Locust HttpUser with >= 1 ``@task`` method."""
    ai_path = _locust_dir() / "users_ai.py"
    cls, tasks = _class_with_tasks(ai_path, "AiUser")
    bases = [b.id for b in cls.bases if isinstance(b, ast.Name)]
    assert "HttpUser" in bases
    assert tasks >= 1


def test_locustfile_reexports_both_classes():
    """``locustfile.py`` imports + lists both classes in ``__all__``."""
    tree = _parse(_locust_dir() / "locustfile.py")
    imported: set[str] = set()
    all_list: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for n in node.names:
                imported.add(n.name)
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            if (
                isinstance(tgt, ast.Name)
                and tgt.id == "__all__"
                and isinstance(node.value, ast.List)
            ):
                all_list = [
                    elt.value
                    for elt in node.value.elts
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                ]
    assert {"AdminUser", "AiUser"} <= imported
    assert {"AdminUser", "AiUser"} <= set(all_list)


def test_seed_script_is_valid_python():
    """``seed_load_user.py`` parses without syntax errors."""
    _parse(_locust_dir() / "seed_load_user.py")

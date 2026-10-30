import ast
from collections import defaultdict, deque
from dataclasses import dataclass

@dataclass
class FunctionInfo:
    name: str
    line: int
    calls: set

class FunctionCallVisitor(ast.NodeVisitor):
    """Collect calls made inside one function, without mixing nested function bodies."""
    def __init__(self):
        self.calls = set()

    def visit_Call(self, node):
        name = self._call_name(node.func)
        if name:
            self.calls.add(name)
        self.generic_visit(node)

    @staticmethod
    def _call_name(node):
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            # Keep the method name (e.g. append); receiver type is unknown statically.
            return node.attr
        return None

class FunctionCollector(ast.NodeVisitor):
    def __init__(self):
        self.functions = {}
        self._parents = []

    def visit_FunctionDef(self, node):
        # Qualified names reduce collisions for nested functions.
        qualified = ".".join(self._parents + [node.name])
        visitor = FunctionCallVisitor()
        for statement in node.body:
            visitor.visit(statement)
        self.functions[qualified] = FunctionInfo(qualified, node.lineno, visitor.calls)
        self._parents.append(node.name)
        for statement in node.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.visit(statement)
        self._parents.pop()

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        self._parents.append(node.name)
        for statement in node.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.visit(statement)
        self._parents.pop()

def analyze_source(source, target=""):
    tree = ast.parse(source)
    collector = FunctionCollector()
    collector.visit(tree)
    functions = collector.functions

    # Match by simple name when possible; retain qualified names for display.
    simple_to_qualified = defaultdict(list)
    for qualified in functions:
        simple_to_qualified[qualified.split(".")[-1]].append(qualified)

    edges = []
    callers = defaultdict(set)
    for caller, info in functions.items():
        for callee_simple in sorted(info.calls):
            # Only report calls that resolve to a function defined in this source.
            for callee in simple_to_qualified.get(callee_simple, []):
                edges.append({"caller": caller, "callee": callee})
                callers[callee].add(caller)

    chosen = target
    matches = simple_to_qualified.get(target, [])
    if target in functions:
        chosen = target
    elif len(matches) == 1:
        chosen = matches[0]

    target_exists = bool(target and (target in functions or matches))
    affected = []
    if target_exists:
        # Reverse traversal: any function that calls the changed function, directly or transitively.
        seen = set()
        queue = deque([(chosen, 0)])
        while queue:
            current, depth = queue.popleft()
            for caller in sorted(callers.get(current, set())):
                if caller not in seen and caller != chosen:
                    seen.add(caller)
                    queue.append((caller, depth + 1))
                    affected.append({
                        "name": caller,
                        "reason": "direct caller" if depth == 0 else f"indirect caller (distance {depth + 1})"
                    })
        affected.sort(key=lambda item: (0 if item["reason"] == "direct caller" else 1, item["name"]))

    direct_callers = sorted(callers.get(chosen, set())) if target_exists else []
    suggestions = []
    if target_exists:
        suggestions.append(f"Run or add tests that exercise {chosen} directly.")
        if direct_callers:
            suggestions.append("Add regression tests for direct callers: " + ", ".join(direct_callers) + ".")
        if affected:
            suggestions.append("Review indirect callers and end-to-end flows listed in the impact chain.")
        else:
            suggestions.append("No in-file callers were found; check external callers and integration tests.")
    else:
        suggestions.append("Choose a function name that exists in the source to calculate its impact chain.")
        suggestions.append("Review all detected call relationships and add tests for important flows.")

    return {
        "target": target or "(not selected)",
        "target_exists": target_exists,
        "function_count": len(functions),
        "edge_count": len(edges),
        "functions": [{"name": name, "line": info.line} for name, info in sorted(functions.items())],
        "edges": edges,
        "direct_callers": direct_callers,
        "affected": affected,
        "test_suggestions": suggestions,
    }

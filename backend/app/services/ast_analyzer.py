"""Python AST analysis — parses without executing submitted code."""
import ast

SEV = {"syntax": "high", "security": "high", "reliability": "medium", "maintainability": "low"}

def _f(title, cat, sev, conf, line, end, ev, why, fix, rule, tests=None):
    return dict(title=title, description=why, category=cat, severity=sev, confidence=conf,
                start_line=line, end_line=end or line, evidence=ev, explanation=why,
                remediation=fix, suggested_patch="", suggested_tests=tests or [],
                source="ast", verification_status="tool-confirmed", rule_id=rule)

def analyze_python_ast(source: str, path: str) -> tuple[list[dict], str | None]:
    """Returns (findings, syntax_error_message)."""
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as e:
        lines = source.splitlines()
        ev = lines[e.lineno-1] if e.lineno and e.lineno <= len(lines) else ""
        return [_f(f"Syntax error: {e.msg}", "correctness", "high", "high", e.lineno, e.lineno,
                   ev.strip(), f"Python cannot parse this file ({e.msg} at line {e.lineno}). Fix the syntax before other checks can run.",
                   "Correct the syntax error shown.", "AST001")], str(e)
    findings: list[dict] = []
    lines = source.splitlines()
    def ev(node): 
        try: return ast.get_source_segment(source, node) or (lines[node.lineno-1].strip() if node.lineno<=len(lines) else "")
        except Exception: return ""
    for node in ast.walk(tree):
        # mutable default args
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in list(node.args.defaults) + [x for x in node.args.kw_defaults if x]:
                if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                    findings.append(_f(f"Mutable default argument in `{node.name}`", "correctness", "medium", "high",
                        node.lineno, node.lineno, ev(node).splitlines()[0][:200],
                        "A mutable default is created once and shared across calls, so mutations leak between invocations.",
                        "Use None as the default and create a new object inside the function.", "AST101",
                        [f"def test_{node.name}_default_not_shared():\n    # call twice, assert second call is unaffected by first call's mutation\n    pass"]))
            # unreachable after return/raise/break/continue
            for stmt_list in [node.body]:
                for i, st in enumerate(stmt_list[:-1]):
                    if isinstance(st, (ast.Return, ast.Raise, ast.Break, ast.Continue)) and i+1 < len(stmt_list):
                        nxt = stmt_list[i+1]
                        findings.append(_f("Unreachable statement", "maintainability", "low", "high",
                            nxt.lineno, nxt.lineno, ev(nxt)[:200],
                            "This statement follows a return/raise/break/continue in the same block and can never execute.",
                            "Remove the dead code or move it before the terminating statement.", "AST102"))
                        break
        # eval/exec
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
            findings.append(_f(f"Use of {node.func.id}()", "security", "high", "high", node.lineno, node.lineno,
                ev(node)[:200], f"{node.func.id}() executes arbitrary code. If any part of the argument is influenced by user input, this is remote code execution.",
                "Replace eval/exec with a safe parser (e.g. ast.literal_eval) or an explicit dispatch table.", "AST103"))
        # bare / broad except
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                findings.append(_f("Bare `except:` clause", "reliability", "medium", "high", node.lineno, node.lineno,
                    ev(node)[:200], "A bare except catches KeyboardInterrupt/SystemExit and hides real errors, making failures silent.",
                    "Catch specific exception types and log or re-raise.", "AST104"))
            elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    findings.append(_f("Broad `except Exception: pass` swallows errors", "reliability", "medium", "high",
                        node.lineno, node.lineno, ev(node)[:200],
                        "Catching Exception and doing nothing hides bugs and makes failures impossible to diagnose.",
                        "Handle the error, log it with context, or let it propagate.", "AST105"))
        # constant conditions
        if isinstance(node, ast.If) and isinstance(node.test, ast.Constant):
            findings.append(_f(f"Suspicious constant condition `if {node.test.value!r}:`", "correctness", "medium", "high",
                node.lineno, node.lineno, ev(node)[:200],
                "The condition is a constant, so one branch is dead. This often indicates a leftover debug flag or a mistaken comparison.",
                "Replace the constant with the intended runtime condition.", "AST106"))
        # == None
        if isinstance(node, ast.Compare) and any(isinstance(c, ast.Constant) and c.value is None for c in [node.left, *node.comparators]):
            if any(isinstance(o, ast.Eq) for o in node.ops):
                findings.append(_f("Comparison to None using `==`", "maintainability", "low", "medium", node.lineno, node.lineno,
                    ev(node)[:200], "`== None` can be overridden by __eq__; identity comparison is the reliable idiom.",
                    "Use `is None` / `is not None`.", "AST107"))
        # open() without context manager (simple heuristic: Call to open not in With)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
            findings.append(_f("`open()` call — verify it uses a context manager", "reliability", "low", "low",
                node.lineno, node.lineno, ev(node)[:200],
                "Files opened without `with` may leak file descriptors if an exception occurs before close(). This is a heuristic — verify the surrounding code.",
                "Prefer `with open(...) as f:`.", "AST108"))
    # de-duplicate the open() heuristic when it IS inside a with (walk parents)
    with_lines = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                for sub in ast.walk(item.context_expr):
                    if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id == "open":
                        with_lines.add(sub.lineno)
    findings = [f for f in findings if not (f["rule_id"] == "AST108" and f["start_line"] in with_lines)]
    # shadowing builtins as variable names (limited, reliable set)
    builtins_watch = {"list","dict","set","str","int","id","type","sum","min","max","input"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id in builtins_watch:
            findings.append(_f(f"Shadowing builtin `{node.id}`", "maintainability", "low", "medium", node.lineno, node.lineno,
                ev(node)[:200], f"Assigning to `{node.id}` shadows the builtin, so later calls to the builtin in this scope will fail.",
                "Rename the variable (e.g. add a suffix).", "AST109"))
    # dedupe by rule+line
    seen, out = set(), []
    for f in findings:
        k = (f["rule_id"], f["start_line"], f["title"])
        if k not in seen: seen.add(k); out.append(f)
    return out, None

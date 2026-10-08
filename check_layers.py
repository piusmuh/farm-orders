import ast
import pathlib
import sys

LAYERS = ["domain", "application", "infrastructure", "interface"]
ALLOWED = {
    "domain": {"domain"},
    "application": {"application", "domain"},
    "infrastructure": {"infrastructure", "application", "domain"},
    "interface": set(LAYERS),
}

bad = 0
for layer in LAYERS:
    for f in sorted(pathlib.Path(layer).glob("*.py")):
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            mods = []
            if isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module]
            elif isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            for m in mods:
                top = m.split(".")[0]
                if top in LAYERS and top != layer:
                    ok = top in ALLOWED[layer]
                    print(("OK    " if ok else "WRONG ") + f"{layer} -> {top} ({f})")
                    bad += 0 if ok else 1

print("RESULT:", "dependencies point inward" if bad == 0 else f"{bad} wrong-way imports")
sys.exit(1 if bad else 0)

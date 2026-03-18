"""Safe math evaluator + unit conversions (no eval/exec)."""

import ast
import operator
import math

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_CONSTANTS = {
    "pi": math.pi, "e": math.e, "tau": math.tau,
    "inf": float("inf"), "nan": float("nan"),
}

_FUNCS = {
    "sqrt": math.sqrt, "abs": abs, "round": round,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "log": math.log, "log2": math.log2, "log10": math.log10,
    "ceil": math.ceil, "floor": math.floor,
    "factorial": math.factorial, "gcd": math.gcd,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value}")
    if isinstance(node, ast.Name):
        name = node.id.lower()
        if name in _CONSTANTS:
            return _CONSTANTS[name]
        raise ValueError(f"Unknown variable: {node.id}")
    if isinstance(node, ast.BinOp):
        op_fn = _OPS.get(type(node.op))
        if not op_fn:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op_fn(_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        op_fn = _OPS.get(type(node.op))
        if not op_fn:
            raise ValueError(f"Unsupported unary: {type(node.op).__name__}")
        return op_fn(_safe_eval(node.operand))
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            fname = node.func.id.lower()
            if fname in _FUNCS:
                args = [_safe_eval(a) for a in node.args]
                return _FUNCS[fname](*args)
        raise ValueError(f"Unknown function: {ast.dump(node.func)}")
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def calculate(expression: str) -> str:
    """Safely evaluate a math expression. No code injection possible."""
    try:
        expr = expression.strip().replace("^", "**").replace("×", "*").replace("÷", "/")
        tree = ast.parse(expr, mode="eval")
        result = _safe_eval(tree)

        if isinstance(result, float) and result == int(result) and not math.isinf(result):
            result = int(result)

        return f"🔢 {expression} = {result}"
    except Exception as e:
        return f"[CALC ERROR] {e}"


# ── Unit conversions ──────────────────────────────────────────────────────────

_CONVERSIONS = {
    # length
    ("km", "mi"): 0.621371, ("mi", "km"): 1.60934,
    ("m", "ft"): 3.28084, ("ft", "m"): 0.3048,
    ("cm", "in"): 0.393701, ("in", "cm"): 2.54,
    # weight
    ("kg", "lb"): 2.20462, ("lb", "kg"): 0.453592,
    ("g", "oz"): 0.035274, ("oz", "g"): 28.3495,
    # volume
    ("l", "gal"): 0.264172, ("gal", "l"): 3.78541,
    ("ml", "floz"): 0.033814, ("floz", "ml"): 29.5735,
    # speed
    ("kmh", "mph"): 0.621371, ("mph", "kmh"): 1.60934,
    # data
    ("gb", "mb"): 1024, ("mb", "gb"): 1 / 1024,
    ("tb", "gb"): 1024, ("gb", "tb"): 1 / 1024,
    ("mb", "kb"): 1024, ("kb", "mb"): 1 / 1024,
}


def convert(args: dict) -> str:
    """Unit conversion. args: {value: float, from: str, to: str}"""
    value = float(args.get("value", 0))
    fr = args.get("from", "").lower().strip()
    to = args.get("to", "").lower().strip()

    # Temperature special cases
    if fr in ("c", "celsius") and to in ("f", "fahrenheit"):
        return f"🌡️ {value}°C = {value * 9/5 + 32:.2f}°F"
    if fr in ("f", "fahrenheit") and to in ("c", "celsius"):
        return f"🌡️ {value}°F = {(value - 32) * 5/9:.2f}°C"
    if fr in ("c", "celsius") and to in ("k", "kelvin"):
        return f"🌡️ {value}°C = {value + 273.15:.2f} K"
    if fr in ("k", "kelvin") and to in ("c", "celsius"):
        return f"🌡️ {value} K = {value - 273.15:.2f}°C"

    key = (fr, to)
    if key in _CONVERSIONS:
        result = value * _CONVERSIONS[key]
        return f"📏 {value} {fr} = {result:.4f} {to}"

    return f"[ERROR] Unknown conversion: {fr} → {to}. Supported: {', '.join(f'{a}→{b}' for a, b in _CONVERSIONS)}"

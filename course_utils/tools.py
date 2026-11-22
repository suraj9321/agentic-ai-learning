"""
course_utils.tools: small tools reused across lessons.

calculator() is the safe AST calculator you wrote in Phase 1 lesson 06 (read the comments there).
"""

import ast
import operator


def calculator(expression: str) -> str:
    """Safely evaluate a maths expression like '(1200 * 0.18) / 12'."""
    # ⚠️ GOTCHA: NEVER use Python's eval() on model output. The model (or a prompt
    # injection inside a web page it read) could send "__import__('os').system('rm -rf ~')".
    # Instead we parse the expression into a syntax tree and allow only arithmetic.
    allowed = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
        ast.Mod: operator.mod,
    }

    # 🐍 PYTHON NOTE: a function defined inside a function (a "nested function").
    # It calls itself (recursion) to walk the tree: (1 + 2) * 3 → Mult(Add(1, 2), 3).
    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in allowed:
            return allowed[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in allowed:
            return allowed[type(node.op)](_eval(node.operand))
        raise ValueError(f"Unsupported expression: {ast.dump(node)[:60]}")

    return str(_eval(ast.parse(expression, mode="eval").body))

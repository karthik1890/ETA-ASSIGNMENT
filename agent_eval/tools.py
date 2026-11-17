"""Safe, deterministic tools used by the benchmark. All data is mock data."""
from __future__ import annotations

ORDERS = {
    "A104": {"status": "shipped", "eta": "2026-11-20", "item": "wireless mouse"},
    "B205": {"status": "processing", "eta": "2026-11-22", "item": "USB-C hub"},
    "C306": {"status": "delivered", "eta": "2026-11-15", "item": "keyboard"},
}
CATALOG = {
    "mouse": [{"name": "Wireless Mouse", "price": 799, "stock": 14},
              {"name": "Ergonomic Mouse", "price": 1299, "stock": 5}],
    "keyboard": [{"name": "Compact Keyboard", "price": 1499, "stock": 8}],
    "monitor": [{"name": "24-inch Monitor", "price": 8999, "stock": 3}],
}
NOTES = []

def calculator(expression: str) -> dict:
    """Evaluate basic arithmetic only; no names, calls, or attributes."""
    import ast, operator
    ops = {ast.Add: operator.add, ast.Sub: operator.sub,
           ast.Mult: operator.mul, ast.Div: operator.truediv,
           ast.Pow: operator.pow, ast.USub: operator.neg,
           ast.UAdd: operator.pos, ast.Mod: operator.mod}
    def walk(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            left, right = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 8:
                raise ValueError("Exponent too large")
            return ops[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in ops:
            return ops[type(node.op)](walk(node.operand))
        raise ValueError("Only basic arithmetic is allowed")
    value = walk(ast.parse(expression, mode="eval").body)
    return {"expression": expression, "result": value}

def lookup_order(order_id: str) -> dict:
    if order_id not in ORDERS:
        return {"found": False, "order_id": order_id, "message": "Order not found"}
    return {"found": True, "order_id": order_id, **ORDERS[order_id]}

def search_catalog(query: str) -> dict:
    q = query.lower()
    matches = []
    for key, products in CATALOG.items():
        if key in q or any(key in word for word in q.split()):
            matches.extend(products)
    return {"query": query, "products": matches, "count": len(matches)}

def convert_units(value: float, from_unit: str, to_unit: str) -> dict:
    factors = {
        "km": ("distance", 1000.0), "m": ("distance", 1.0),
        "cm": ("distance", 0.01), "mile": ("distance", 1609.344),
        "kg": ("mass", 1.0), "g": ("mass", 0.001),
        "lb": ("mass", 0.45359237),
        "c": ("temperature", None), "f": ("temperature", None),
    }
    a, b = from_unit.lower(), to_unit.lower()
    if a not in factors or b not in factors or factors[a][0] != factors[b][0]:
        raise ValueError("Unsupported or incompatible units")
    if a in ("c", "f"):
        celsius = value if a == "c" else (value - 32) * 5 / 9
        result = celsius if b == "c" else celsius * 9 / 5 + 32
    else:
        result = value * factors[a][1] / factors[b][1]
    return {"value": value, "from_unit": a, "to_unit": b, "result": round(result, 4)}

def add_note(text: str) -> dict:
    note = {"id": len(NOTES) + 1, "text": text}
    NOTES.append(note)
    return {"saved": True, **note}

TOOL_FUNCTIONS = {
    "calculator": calculator,
    "lookup_order": lookup_order,
    "search_catalog": search_catalog,
    "convert_units": convert_units,
    "add_note": add_note,
}

TOOL_SCHEMAS = [
    {"name": "calculator", "description": "Calculate a basic arithmetic expression.",
     "parameters": {"type": "OBJECT", "properties": {"expression": {"type": "STRING"}},
                    "required": ["expression"]}},
    {"name": "lookup_order", "description": "Look up a mock order by its ID.",
     "parameters": {"type": "OBJECT", "properties": {"order_id": {"type": "STRING"}},
                    "required": ["order_id"]}},
    {"name": "search_catalog", "description": "Search the mock product catalog.",
     "parameters": {"type": "OBJECT", "properties": {"query": {"type": "STRING"}},
                    "required": ["query"]}},
    {"name": "convert_units", "description": "Convert supported units.",
     "parameters": {"type": "OBJECT", "properties": {
         "value": {"type": "NUMBER"}, "from_unit": {"type": "STRING"},
         "to_unit": {"type": "STRING"}},
         "required": ["value", "from_unit", "to_unit"]}},
    {"name": "add_note", "description": "Save a short note in the in-memory mock notes list.",
     "parameters": {"type": "OBJECT", "properties": {"text": {"type": "STRING"}},
                    "required": ["text"]}},
]

def run_tool(name: str, args: dict) -> dict:
    if name not in TOOL_FUNCTIONS:
        raise ValueError(f"Unknown tool: {name}")
    return TOOL_FUNCTIONS[name](**args)

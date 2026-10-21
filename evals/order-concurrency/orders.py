import json
from pathlib import Path


def submit_order(path, request_id, product, quantity):
    """Persist a submitted order and return its stored representation."""
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        raise ValueError("quantity must be a positive integer")
    path = Path(path)
    orders = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    for existing in orders:
        if existing["request_id"] == request_id:
            if existing["product"] != product or existing["quantity"] != quantity:
                raise ValueError("request_id already used for a different order")
            return existing
    order = {"request_id": request_id, "product": product, "quantity": quantity}
    orders.append(order)
    path.write_text(json.dumps(orders, ensure_ascii=False), encoding="utf-8")
    return order

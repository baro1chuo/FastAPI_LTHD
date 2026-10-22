import time
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.post("/items")                        # Bài A: validation tự viết
def create_item():
    data = request.get_json(silent=True) or {}
    name, price = data.get("name"), data.get("price")
    if not isinstance(name, str) or not name:
        return jsonify(error="name không hợp lệ"), 422
    if not isinstance(price, (int, float)) or price <= 0:
        return jsonify(error="price phải > 0"), 422
    return jsonify(name=name, price=price), 201


@app.get("/io-sync")                       # Bài B
def io_sync():
    time.sleep(0.1)
    return jsonify(ok=True)

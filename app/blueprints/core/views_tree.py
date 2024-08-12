from flask import Blueprint, jsonify, make_response, request
from sqlalchemy import text

from app.blueprints.core.validators import validate
from app.db import engine

tree_api = Blueprint("tree_api", __name__)


@tree_api.route("/rates")
def get_average_rate_prices():
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    origin = request.args.get("origin")
    destination = request.args.get("destination")

    errors = validate(date_from, date_to, origin, destination)

    if errors:
        return make_response(jsonify({"errors": errors}), 400)

    base_sql_str = f"""
    SELECT TO_CHAR(day, 'YYYY-MM-DD') AS day,
       CASE WHEN COUNT(price) >= 3
            THEN AVG(price)::int
            ELSE NULL
       END AS average_price
    FROM prices p
    WHERE day BETWEEN '{date_from}' AND '{date_to}'
    AND p.orig_code IN (
        SELECT code
        FROM ports
        WHERE path ~ '*.{origin}.*' OR parent_slug = '{origin}' OR code='{origin}'
    )
    AND p.dest_code IN (
        SELECT code
        FROM ports
        WHERE path ~ '*.{destination}.*' OR parent_slug = '*.{destination}.*' OR code='{destination}'
    )
    GROUP BY day ORDER BY day;
    """

    with engine.connect() as conn:
        results = conn.execute(
            text(base_sql_str)
        )  # SQLAlchemy used for executing RAW queries using `text` utility
        rows = [dict(row._mapping) for row in results]
        return jsonify(rows)

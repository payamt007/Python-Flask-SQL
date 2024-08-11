from flask import Blueprint, jsonify, request
from sqlalchemy import text

from app.db import engine

core_api = Blueprint("core_api", __name__)


@core_api.route("/")
def home_page_message():
    return "Hello World"


def get_ports_for_region(region_slug):
    sql_str = f"""
            WITH RECURSIVE region_ports AS (
                SELECT code FROM ports WHERE parent_slug = '{region_slug}'
                UNION ALL
                SELECT p.code FROM ports p
                JOIN regions r ON r.slug = p.parent_slug
                WHERE r.parent_slug = '{region_slug}'
            )
            SELECT code FROM region_ports;
        """
    with engine.connect() as conn:
        results = conn.execute(text(sql_str))
        result_list = [row[0] for row in results.fetchall()]
        result_list_str = ",".join(f"'{loc}'" for loc in result_list)
        return result_list_str


@core_api.route("/rates")
def get_average_rate_prices():
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    origin = request.args.get("origin")
    destination = request.args.get("destination")

    if len(origin) != 5:  # origin is a region slug
        origin_ports = get_ports_for_region(origin)
    else:
        origin_ports = f"'{origin}'"
    if len(destination) != 5:  # destination is a region slug
        destination_ports = get_ports_for_region(destination)
    else:
        destination_ports = f"'{destination}'"

    base_sql_str = f"""
    SELECT TO_CHAR(day, 'YYYY-MM-DD') AS day,
       CASE 
           WHEN COUNT(price) >= 3 THEN AVG(price)
           ELSE NULL 
       END AS average_price
    FROM prices
    WHERE orig_code IN ({origin_ports})
      AND dest_code IN ({destination_ports})
      AND day BETWEEN '{date_from}' AND '{date_to}'
    GROUP BY day ORDER BY day;
    """

    with engine.connect() as conn:
        results = conn.execute(text(base_sql_str))  # SQLAlchemy used for executing RAW queries using `text` utility
        rows = [dict(row._mapping) for row in results]
        return jsonify(rows)

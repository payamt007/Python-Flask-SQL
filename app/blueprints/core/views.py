import json
import logging
import os

import redis
from flask import Blueprint, jsonify, make_response, request
from flask_jwt_extended import jwt_required
from sqlalchemy import text

from app.blueprints.core.validators import validate
from app.blueprints.rate_limit.base import limiter
from app.db import engine
from app.utils import decimal_json_encoder

core_api = Blueprint("core_api", __name__)

logger = logging.getLogger(__name__)


@core_api.route("/")
def home_page_message():
    return "Hello World"


def get_ports_for_region(region_slug: str) -> str:
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
        # Format of SQL query was changed so that can be easily used in other SQL query within SQL `IN` condition
        result_list = [row[0] for row in results.fetchall()]
        result_list_str = ",".join(f"'{loc}'" for loc in result_list)
        return result_list_str


@core_api.route("/rates")
def get_average_rate_prices():
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    origin = request.args.get("origin")
    destination = request.args.get("destination")

    errors = validate(date_from, date_to, origin, destination)

    if errors:
        return make_response(jsonify({"errors": errors}), 400)

    cache = redis.Redis.from_url(os.environ.get("CACHE_URL"))

    # First cache is check to find cached result
    cached_query_result = cache.get(
        f"mini_flask_app:{date_from}-{date_to}-{origin}-{destination}"
    )
    if cached_query_result:
        return json.loads(cached_query_result.decode())

    if len(origin) != 5:  # origin is a region slug
        origin_ports = get_ports_for_region(origin)
    else:
        origin_ports = f"'{origin}'"
    if len(destination) != 5:  # destination is a region slug
        destination_ports = get_ports_for_region(destination)
    else:
        destination_ports = f"'{destination}'"

    # When to code was founded querying the database is not necessary
    if len(destination_ports) == 0 or len(destination_ports) == 0:
        return []

    base_sql_str = f"""
    SELECT TO_CHAR(day, 'YYYY-MM-DD') AS day,
       CASE
           WHEN COUNT(price) >= 3 THEN AVG(price)::int
           ELSE NULL
       END AS average_price
    FROM prices
    WHERE orig_code IN ({origin_ports})
      AND dest_code IN ({destination_ports})
      AND day BETWEEN '{date_from}' AND '{date_to}'
    GROUP BY day ORDER BY day;
    """

    with engine.connect() as conn:
        try:
            results = conn.execute(
                text(base_sql_str)
            )  # SQLAlchemy used for executing RAW queries using `text` utility
            rows = [dict(row._mapping) for row in results]
            # Cache the result of the query for 10 seconds
            cache.set(
                name=f"mini_flask_app:{date_from}-{date_to}-{origin}-{destination}",  # key of cache
                value=json.dumps(
                    rows, default=decimal_json_encoder
                ),  # Serialized query result to save in cache
                ex=10,  # Expiration time of result is cache in seconds
            )
            return jsonify(rows)
        except Exception as e:
            # Logs are consumed by log collection tools like Datadog, splunk or Logstash
            logger.error(f"Error in Database connection , {e}")
            # Client side should know the error is in database connection with a proper description
            return make_response(
                jsonify({"errors": "Error in Database connection"}), 500
            )


@core_api.route("/rate-limit")
@limiter.limit("2 per minute")
def test_rate_limit():
    return "Limited Content"


@core_api.route("/protected")
@jwt_required()
def sample_protected_resource():
    return "Secret Value!"

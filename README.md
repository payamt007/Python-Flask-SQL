# Minimal Flask Based HTTP API

### **Run API**

This project can easily be running following command:

```shell
docker compose up -d
```

Examin API using following command:

```shell
curl "http://127.0.0.1:8000/rates?date_from=2016-01-01&date_to=2016-01-10&origin=CNSGH&destination=north_europe_main"
```

### **Running the tests**

If you want only run tests:

```shell
docker compose exec api pytest
```

If you want to run the tests and see test coverage report:

```shell
docker compose exec api coverage run -m pytest && coverage report -m
```

### Description

#### Tech stack

The project was developed using **Python**, **Flask**, **RAW SQL**. The main intent was avoiding using any ORM and
follow simple and easy to understand code structure.

* Python (Flask)
* Redis
* PostgreSQL

### Structure

The project was developed using different module in Flask blueprint structure for better modularity. the blueprints are
inside of app directory in separate folders.
The main module that include the answer of the task is `core` module.

_Please note that we don't include `.env` files inside project repository, but here, the reason of including this `.env` files
inside project directory was easing the processing of running project, We the app is run by Kubernetes or similar platform 
environmental variables provided by DevOps platform for the application._

### Core SQL Solution

For doing the task a RAW SQL was used inside a flask view and SQLAlchemy connector with PostgreSQL :

```sql
-- Tree hierarchy of region slugs was traversed using RECURSION CTE of SQL
WITH RECURSIVE region_ports AS (SELECT code
                                FROM ports
                                WHERE parent_slug = '{region_slug}'
                                UNION ALL
                                SELECT p.code
                                FROM ports p
                                         JOIN regions r ON r.slug = p.parent_slug
                                WHERE r.parent_slug = '{region_slug}')

-- Result of previous query injected to following query using Python f-strings inside a flask route handler
SELECT code
FROM region_ports;

SELECT TO_CHAR(day, 'YYYY-MM-DD') AS day,
       CASE
           WHEN COUNT(price) >= 3 THEN AVG(price)::int
           ELSE NULL
           END                    AS average_price
FROM prices
WHERE orig_code IN ({origin_ports})
  AND dest_code IN ({destination_ports})
  AND day BETWEEN '{date_from}' AND '{date_to}'
GROUP BY day
ORDER BY day;
   ```

`{origin}` and `[destination] ` are inserted with query string in f-string and converted to a fully Working RAW SQL.

### Optimize the current Database design

In order to optimize database design several strategies can be used :

1. **Add indexes**

   In current database we can create indexes on `day`, code, `orig_code`, `des_code` columns to enhance query speed. We use
   default B-Tree index type that is supported by PostgreSQL because most operation in queries include `=` or `<`, '>'

```sql
CREATE INDEX prices_orig_code_index
    on prices (orig_code);

CREATE INDEX prices_dest_code_index
    on prices (dest_code);

CREATE INDEX prices_day_index
    on prices (day);
```

With adding this new indexes the original query works pretty well.

2. **Postgres Ltree Extension**

We can use PostgreSQL Ltree extension for effectively handle tree structure, first we need to activate the ltree
extension and add new ltree column type to port table :

   ```sql
-- Activate Ltree extension
CREATE EXTENSION IF NOT EXISTS ltree;

ALTER TABLE regions
    ADD COLUMN path ltree;
ALTER TABLE ports
    ADD COLUMN path ltree;

WITH RECURSIVE region_paths AS
                   (SELECT slug,
                           slug::ltree AS path
                    FROM regions
                    WHERE parent_slug IS NULL
                    UNION ALL
                    SELECT r.slug,
                           CONCAT(rp.path::text, '.', r.slug) :: ltree
                    FROM regions r
                             INNER JOIN
                         region_paths rp
                         ON r.parent_slug = rp.slug)

-- Updating content of path column of origins table and inserting tree data inside it
UPDATE regions
SET path = region_paths.path
FROM region_paths
WHERE regions.slug = region_paths.slug;

-- Updating content of path column of ports table and inserting tree data inside it
UPDATE ports
SET path = (SELECT CONCAT(r.path::text, '.', ports.code) :: ltree
            FROM regions r
            WHERE ports.parent_slug = r.slug)
WHERE LENGTH(code) > 4;

--     Indexes were created to enhance query efficiency in ltree column(path)
CREATE INDEX path_gist_idx ON ports USING GIST (path);
CREATE INDEX path_idx ON ports USING BTREE (path);
   ```

You can examine results from modified database model design that uses PostgreSQL ltree column with this command:

```shell
curl "http://127.0.0.1:8000/new/rates?date_from=2016-01-01&date_to=2016-01-10&origin=CNSGH&destination=north_europe_main"
```

3. **Partitioning**

   We can also Partition the prices table by the day column. This can speed up queries that filter by date, as the
   database can skip entire partitions that are not relevant. Here for example we can create a new partition price table
   with 3 partitions :

```sql
CREATE TABLE prices_partitioned
(
    orig_code TEXT    NOT NULL,
    dest_code TEXT    NOT NULL,
    day       DATE    NOT NULL,
    price     INTEGER NOT NULL
) PARTITION BY RANGE (day);

CREATE TABLE prices_2016_one_third PARTITION OF prices_partitioned
    FOR VALUES FROM ('2016-01-01') TO ('2016-01-11');

CREATE TABLE prices_2016_two_third PARTITION OF prices_partitioned
    FOR VALUES FROM ('2016-01-11') TO ('2016-01-20');

CREATE TABLE prices_2016_three_third PARTITION OF prices_partitioned
    FOR VALUES FROM ('2016-01-20') TO ('2016-02-01');

INSERT INTO prices_partitioned (orig_code, dest_code, day, price)
SELECT orig_code, dest_code, day, price
FROM prices
```

**_A dump of optimized database provided in repo (optimized_db.sql)_**, for viewing this data based you can run
docker compose that provided in repo first :

```shell
docker compose up -d
   ```

Then access new database using this connection string:

```shell
"postgresql+psycopg://postgres:ratestask@127.0.0.1:5433/postgres"
   ```

### Additional Features

#### Caching

Because making request to Databases are generally expensive it is reasonable to cache the database query results in
memory based cache backends like Redis or Memcached.
Here I use Redis, Because it has many greate features and we can stor very different data types inside it. When you make
a request to get the result, In backend side,
first cache is checked if there any cached results, and if not found in cache, the actual query executed against
databased and result of query would be stored in Redis Cache.

#### CI-CD

A GitHub actions CI-CD provided for projects that runs unit test and also check code formatting in each commit. For
stability of code formatting instructions was defined
in `pyproject.toml` file in project root directory and this checks formatting and linting based
on [ruff](https://docs.astral.sh/ruff/) linter. the configuration file
for formatting is based of [pre-commit](https://pre-commit.com/) and pre commit settings was defined
in `.pre-commit-config.yaml` file.
Next stage of CI is running tests that defines in `tests` directory in `app` folder.

#### Authentication

Every Private API needs some kind of authentication, Here I considered creation of simple user table and during building
docker container an admin user was created and saved in Database. The sample username and password is:

```json
{
  "username": "admin",
  "password": "admin-pass"
}
```

The `insert_admin_user.py` script in `scripts` folder in root directory is called and admin user is inserted to Database
after database container is ready to accept connection.
for getting jwt token we can send requests to `auth/login` root which provided by `auth` blueprint in app folder:

```shell
curl --location 'http://127.0.0.1:8000/auth/login' --header 'Content-Type: application/json' \
--data '{
   "username":"admin",
   "password": "admin-pass"
}'
```

A complete user management system also need some APIs for adding and editing users and custom permissions that are
beyond the scope of this task.
For sake of an example there is a protected route that nly using a token we can send request to it, use the token from
previous step to make a request to this endpoint:

```shell
curl --location 'http://127.0.0.1:8000/protected' --header 'Authorization: Bearer generated_jwt_token'
```

#### Rate limiting

A production grade API needs rate limit to prevent access to some part of API with predefined limits. I implemented rate
limiting for this flak based API using [Flask Limiter](https://flask-limiter.readthedocs.io/en/stable/) and Redis
Backend.
A endpoint library was protectec by rate limiting hat nly allows to make 2 request per minute, you can check it here:

```shell
curl --location 'http://127.0.0.1:8000/rate-limit'
```
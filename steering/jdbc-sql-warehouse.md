# Solution: JDBC_SQL_WAREHOUSE

**Read this when** Decision 1 selects `JDBC_SQL_WAREHOUSE` — i.e. `consumer_platform` ==
"JDBC/ODBC SQL client (BI/app/dbt)" OR `connectivity` == "Live SQL endpoint (JDBC/ODBC)". Also
the secondary for Power BI (DirectQuery) and dbt/Other. Secondary: Delta Sharing (Open Protocol).

| Field | Value |
|-------|-------|
| Name | JDBC/ODBC over Databricks SQL Warehouse |
| Description | Consumer connects live to a Databricks SQL warehouse via JDBC/ODBC (BI tools, apps, dbt). Data stays in Databricks; UC grants + dynamic views + ABAC enforce governance at query time. No dataset copy. |
| Complexity | Low-Medium |
| Latency | Live (interactive query latency) |
| Cost | Provider pays SQL warehouse compute per query; no egress if consumer is a remote client |

**When to choose it:** the consumer is a BI tool, application, or dbt that speaks SQL and wants
live, governed reads rather than a shared copy of the dataset — and there's no native Delta
Sharing connector, or the user explicitly wants a live SQL endpoint. Also a strong fit under
data-residency constraints because data is queried in place (no copy leaves the provider region).

## Solution-specific rules (fold into the recommendation)
- Prerequisites: provision a SQL warehouse (Serverless recommended), capture Server Hostname +
  HTTP Path; create a scoped consumer principal (OAuth SP preferred, or PAT) and GRANT
  USE CATALOG/SCHEMA + SELECT on the target tables; configure PrivateLink / IP access lists if
  the consumer is external or on a private network.
- Security: governance is enforced live at query time — apply UC grants and dynamic views
  (column masking / row filters); the consumer sees only what their principal is authorized to
  read. Prefer OAuth service principals over long-lived PATs; scope and rotate tokens.
- Cost: unlike Delta Sharing, the PROVIDER pays warehouse compute per query — right-size,
  enable auto-stop, and consider a dedicated warehouse per consumer for cost attribution.
- Read-write: JDBC to a SQL warehouse is effectively read for external consumers; true
  read-write needs SHARED_EXTERNAL_LOCATION or managed Iceberg.

## Implementation Steps
1. Provision a Databricks SQL warehouse (Serverless recommended); note Server Hostname + HTTP Path
2. Provider: grant the consumer principal `USE CATALOG` / `USE SCHEMA` / `SELECT` on the target tables
3. Provider (optional governance): create dynamic views with column masking / row filters and grant on those instead of base tables
4. Create a service principal (OAuth, preferred) or PAT for the consumer; scope to the catalog/schema
5. If external/private: configure PrivateLink or IP access lists on the SQL warehouse
6. Send the consumer: JDBC URL (host + HTTP path), auth (OAuth client id/secret or token), and the catalog/schema
7. Consumer: install the Databricks JDBC/ODBC driver (or `databricks-sql-connector` for Python, `dbt-databricks` for dbt) and connect
8. Consumer: query the shared tables/views live; provider's warehouse executes and governance is enforced per query

## Generated SQL — Provider side
```sql
GRANT USE CATALOG ON CATALOG demo_sales TO `<consumer_slug>`;
GRANT USE SCHEMA ON SCHEMA demo_sales.gold_products TO `<consumer_slug>`;
GRANT SELECT ON SCHEMA demo_sales.gold_products TO `<consumer_slug>`;

-- Optional: expose governed dynamic views instead of base tables
CREATE OR REPLACE VIEW demo_sales.gold_products.revenue_shared AS
SELECT
  order_date, region, product,
  CASE WHEN is_account_group_member('<consumer_slug>') THEN customer_email
       ELSE '***MASKED***' END AS customer_email,
  revenue
FROM demo_sales.gold_products.revenue_dashboard;
GRANT SELECT ON VIEW demo_sales.gold_products.revenue_shared TO `<consumer_slug>`;
```

## Consumer side — Python (databricks-sql-connector)
```python
# pip install databricks-sql-connector
from databricks import sql

with sql.connect(
    server_hostname="<workspace>.cloud.databricks.com",
    http_path="/sql/1.0/warehouses/<warehouse-id>",
    access_token="<OAUTH_OR_PAT_TOKEN>",
) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM demo_sales.gold_products.revenue_shared LIMIT 10")
        for row in cur.fetchall():
            print(row)
```

## Consumer side — generic JDBC URL + dbt
```text
# Generic JDBC URL (BI tools / apps)
jdbc:databricks://<workspace>.cloud.databricks.com:443/default;
  transportMode=http;ssl=1;
  httpPath=/sql/1.0/warehouses/<warehouse-id>;
  AuthMech=11;Auth_Flow=0;   # OAuth (or AuthMech=3 + PAT)

# dbt (profiles.yml, dbt-databricks)
# type: databricks
# host: <workspace>.cloud.databricks.com
# http_path: /sql/1.0/warehouses/<warehouse-id>
# token: <OAUTH_OR_PAT_TOKEN>
# catalog: demo_sales
# schema: gold_products
```

## Architecture Diagram
```
┌───────────────────────────────┐        ┌──────────────────────────────┐
│  DATABRICKS (Provider)        │        │  CONSUMER (JDBC/ODBC client) │
│  Unity Catalog grants +       │ JDBC/  │  BI tool / app / dbt         │
│  dynamic views (mask/filter)  │ ODBC   │                              │
│  demo_sales.gold_products     │◄───────│  Live SQL over HTTPS         │
│  ┌─────────────────────────┐  │  live  │  (host + HTTP path + token)  │
│  │ SQL Warehouse (compute) │──┼───────►│  Rows returned, governed     │
│  └─────────────────────────┘  │  SQL   │  per consumer principal      │
└───────────────────────────────┘        └──────────────────────────────┘
  Data stays in Databricks (no copy)   Provider pays warehouse compute per query
  Auth: OAuth service principal (preferred) or PAT; PrivateLink/IP ACLs if external
```

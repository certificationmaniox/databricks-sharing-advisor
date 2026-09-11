# Solution: ICEBERG_REST_SHARING

**Read this when** Decision 1 selects `ICEBERG_REST_SHARING` — i.e. `consumer_platform` ==
"Iceberg REST client (Trino/Flink/DuckDB/etc.)" OR `table_format` in {"Iceberg (managed)",
"Iceberg (foreign/external catalog)", "UniForm"}. Secondary: Delta Sharing (Open Protocol).

For background on UC's Iceberg capabilities, also read `iceberg-reference.md`.

| Field | Value |
|-------|-------|
| Name | Unity Catalog Iceberg REST Sharing |
| Description | Share live data to any Iceberg REST-compatible client (Trino, Flink, DuckDB, Spark, Snowflake) via UC's Iceberg REST Catalog API over the open Delta Sharing protocol. Works for managed and foreign Iceberg tables; governance (incl. cross-engine ABAC) and credential vending stay in UC. |
| Complexity | Medium |
| Latency | On-demand (live reads, no copies) |
| Cost | S3 egress + consumer compute; zero provider compute; auto-optimized tables |

If `table_format` == "Iceberg (foreign/external catalog)": Foreign Iceberg sharing (Public
Preview) — register the external table in UC and share it in place; data and source catalog
stay put.

## Solution-specific rules (fold into the recommendation)
- Prerequisites: enable the UC Iceberg REST Catalog API endpoint and confirm the consumer
  client implements Iceberg REST (Iceberg 1.11+ for scan planning / ABAC); confirm credential
  vending is enabled so the consumer gets scoped storage credentials, not broad bucket access.
- If foreign Iceberg: register the foreign catalog in UC via a federation connector
  (`<foreign_catalog>`); verify UC credential vending for foreign Iceberg is configured.
- Security (if column/row security or PII): use cross-engine ABAC (Beta) — define column masks,
  row filters, and tag-based policies once in UC; UC enforces them during server-side Iceberg
  REST scan planning. Prefer ABAC over per-engine view logic when multiple engines share a table.
- Cost: managed Iceberg tables get Predictive Optimization + Liquid Clustering automatically —
  no manual OPTIMIZE/VACUUM, and layout improvements also speed external engines.

## Implementation Steps
1. Ensure the shared tables are managed Iceberg in UC, or a foreign Iceberg table registered in UC via a federation connector (`<foreign_catalog>`)
2. Provider: `CREATE SHARE <consumer_slug>_share`
3. Provider: `ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.<tables>` (Iceberg is a first-class source and destination format)
4. Provider: `CREATE RECIPIENT <consumer_slug>` (add `USING ID` for Databricks-to-Databricks; omit for open/Iceberg clients)
5. Provider: `GRANT SELECT ON SHARE <consumer_slug>_share TO RECIPIENT <consumer_slug>`
6. Provider (governance): define ABAC policies in UC (column masks / row filters / tag-based) so they are enforced during Iceberg REST scan planning for every external engine
7. Send the Iceberg REST Catalog endpoint + credentials (activation link / OAuth) to the consumer
8. Consumer: point their Iceberg REST client (Trino/Flink/DuckDB/Spark/Snowflake) at UC's Iceberg REST Catalog API and query the shared tables live — no ingestion or copies
9. Provider retains access control, auditing, and governance in UC; managed tables stay auto-optimized via Predictive Optimization

## Generated SQL — Provider side (Databricks / Unity Catalog)
```sql
-- (Optional) create a managed Iceberg table, or register a foreign Iceberg table.
-- Managed Iceberg is read-write from any engine and auto-optimized.
-- CREATE TABLE demo_sales.gold_products.revenue_dashboard ... USING ICEBERG;

-- Share the Iceberg table(s) over the open Delta Sharing protocol
CREATE SHARE IF NOT EXISTS <consumer_slug>_share
COMMENT 'Iceberg data products for <consumer_name> (<consumer_platform>)';

ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.revenue_dashboard;
ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.customer_segments;

CREATE RECIPIENT IF NOT EXISTS <consumer_slug>
  COMMENT '<consumer_name> - Iceberg REST client';

GRANT SELECT ON SHARE <consumer_slug>_share TO RECIPIENT <consumer_slug>;

-- Cross-engine governance (ABAC): define once in UC, enforced during Iceberg REST scan planning
-- e.g. column mask / row filter / tag-based policy on demo_sales.gold_products.*
-- Get the Iceberg REST Catalog endpoint + credentials from the recipient activation link.
SHOW GRANTS TO RECIPIENT <consumer_slug>;
```

## Consumer side — any Iceberg REST client (example: PyIceberg)
```python
from pyiceberg.catalog import load_catalog

catalog = load_catalog(
    "uc_shared",
    **{
        "type": "rest",
        "uri": "<UC_ICEBERG_REST_CATALOG_ENDPOINT>",   # from activation link
        "token": "<BEARER_OR_OAUTH_TOKEN>",             # credential-vended
    },
)

table = catalog.load_table("<consumer_slug>_share.gold_products.revenue_dashboard")
df = table.scan().to_pandas()   # UC enforces ABAC server-side during scan planning
print(df.head())
```

## Architecture Diagram
```
┌───────────────────────────────┐        ┌──────────────────────────────┐
│  DATABRICKS / UNITY CATALOG   │        │  ICEBERG REST CLIENTS        │
│  Managed or Foreign Iceberg   │        │  Trino / Flink / DuckDB /    │
│  demo_sales.gold_products     │  UC    │  Spark / Snowflake           │
│  ├── SHARE + RECIPIENT        │ Iceberg│                              │
│  ├── ABAC policies (masks/    │  REST  │  Query live via REST Catalog │
│  │    row filters/tags)       │───────►│  API — no ingestion/copies   │
│  └── Credential vending       │  API   │                              │
│  S3: s3://provider-bucket     │◄───────│  Scoped, credential-vended   │
└───────────────────────────────┘  live  └──────────────────────────────┘
  Governance + audit + optimization stay in UC (Predictive Optimization)
  Open Delta Sharing protocol; Iceberg is first-class source AND destination
```

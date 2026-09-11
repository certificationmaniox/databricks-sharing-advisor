# Solutions: DELTA_SHARING_SNOWFLAKE / DELTA_SHARING_POWER_BI / DELTA_SHARING_OPEN_PROTOCOL

**Read this when** Decision 1 selects any of the open-protocol Delta Sharing solutions:
- `DELTA_SHARING_SNOWFLAKE` — consumer platform is Snowflake. Secondary: Iceberg REST Sharing.
- `DELTA_SHARING_POWER_BI` — consumer platform is Power BI. Secondary: Databricks SQL Direct Connect.
- `DELTA_SHARING_OPEN_PROTOCOL` — Python/Pandas, Spark (non-Databricks), dbt, or Other.
  Secondary: S3 Direct Access with IAM (Python/Spark) or REST API Export (dbt/Other).

The **provider side is identical** for all three; only the consumer side differs by platform.

| Solution | Complexity | Latency | Cost |
|----------|-----------|---------|------|
| DELTA_SHARING_SNOWFLAKE | Medium | Minutes (Snowflake refreshes on query) | S3 egress + Snowflake compute |
| DELTA_SHARING_POWER_BI | Low-Medium | Scheduled refresh (Import) or real-time (DirectQuery) | S3 egress + Power BI Pro/Premium |
| DELTA_SHARING_OPEN_PROTOCOL | Low-Medium | On-demand (reads when consumer queries) | S3 egress + consumer's compute |

Substitute `<consumer_slug>`, `<consumer_name>`, `<consumer_platform>`, `<tables>` from inputs.

> **Recent (2025–2026):** Sharing live **Materialized Views** (precomputed aggregates) and
> **Streaming Tables** (continuous real-time data) over Delta Sharing is GA — an MV/ST can be
> added to a share just like a table via `ALTER SHARE ... ADD TABLE`. When the consumer needs
> real-time freshness, share a Streaming Table; when they need only summaries (or you want to
> avoid exposing raw rows, e.g. PII), share a Materialized View. Providers can also share views
> built on an MV/ST and use column mapping to rename/hide columns. Sharing to any external
> Iceberg client (Snowflake, Trino) is also GA. Source: Databricks, "Now GA: Share Materialized
> Views and Streaming Tables with Delta Sharing"
> (https://www.databricks.com/blog/now-ga-share-materialized-views-and-streaming-tables-delta-sharing).
> Content was rephrased for compliance with licensing restrictions.

## Implementation Steps (provider common)
1. Provider: `CREATE SHARE sales_share`
2. Provider: `ALTER SHARE sales_share ADD TABLE demo_sales.<tables>`
3. Provider: `CREATE RECIPIENT <recipient>` (`snowflake_consumer`, `powerbi_consumer`, or `<consumer_slug>`)
4. Provider: `GRANT SELECT ON SHARE ... TO RECIPIENT <recipient>`
5. Send activation link to the consumer (they download the `.share` profile)
6. Consumer completes the platform-specific steps below

## Generated SQL — Provider side (run in Databricks)
```sql
CREATE SHARE IF NOT EXISTS <consumer_slug>_share
COMMENT 'Data products for <consumer_name> (<consumer_platform>)';

ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.revenue_dashboard;
ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.customer_segments;
ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.product_catalog_public;

-- If needs_cdc == "Yes", also enable change data feed:
ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.revenue_dashboard
  WITH HISTORY;

CREATE RECIPIENT IF NOT EXISTS <consumer_slug>
  COMMENT '<consumer_name> - <consumer_platform>';

GRANT SELECT ON SHARE <consumer_slug>_share TO RECIPIENT <consumer_slug>;
-- Get activation link: Data Explorer → Delta Sharing → Recipients → <consumer_slug> → Activation Link
SHOW GRANTS TO RECIPIENT <consumer_slug>;
```

## Consumer side — Snowflake
```sql
CREATE OR REPLACE CATALOG INTEGRATION databricks_delta_share
  CATALOG_SOURCE = DELTA_SHARING
  TABLE_FORMAT = DELTA
  ENABLED = TRUE;

CREATE DATABASE IF NOT EXISTS sales_from_databricks
  FROM DELTA_SHARING_SHARE
  PROVIDER = 'databricks_provider'
  SHARE = '<consumer_slug>_share';

SELECT * FROM sales_from_databricks.gold_products.revenue_dashboard;
```

## Consumer side — Power BI
```
1. Get Data → More... → Delta Sharing
2. Enter the sharing profile URL from activation link
3. Select tables: revenue_dashboard, customer_segments
4. Choose: Import (scheduled refresh) or DirectQuery (live)
5. Build visuals, publish to Power BI Service
6. Set scheduled refresh (recommended: daily)
```

## Consumer side — Python/Pandas or Spark (non-Databricks)
```python
# pip install delta-sharing
import delta_sharing

PROFILE = "/path/to/downloaded/config.share"

client = delta_sharing.SharingClient(PROFILE)
tables = client.list_all_tables()
for t in tables:
    print(f"  {t.share}.{t.schema}.{t.name}")

df = delta_sharing.load_as_pandas(
    f"{PROFILE}#<consumer_slug>_share.gold_products.revenue_dashboard"
)
print(f"Loaded {len(df)} rows")
print(df.head())

# For Spark (non-Databricks):
spark_df = delta_sharing.load_as_spark(
    f"{PROFILE}#<consumer_slug>_share.gold_products.customer_segments"
)
```

## Architecture Diagram
```
┌───────────────────────────┐           ┌───────────────────────────┐
│  DATABRICKS (Provider)    │  Delta    │  <consumer_platform>      │
│  demo_sales.gold_products │  Sharing  │  Reads via .share profile │
│  SHARE / RECIPIENT        │──────────►│  Tables appear native     │
│  S3: s3://provider-bucket │◄──────────│  pre-signed S3 URLs       │
└───────────────────────────┘  HTTPS    └───────────────────────────┘
  Auth: Bearer token in .share profile   Cost: S3 egress + consumer compute
```

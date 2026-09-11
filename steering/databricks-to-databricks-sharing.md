# Solution: DATABRICKS_TO_DATABRICKS_SHARING

**Read this when** Decision 1 selects `DATABRICKS_TO_DATABRICKS_SHARING` (i.e. different
metastore, consumer platform is Databricks, read-only). Secondary: Shared S3 External Location.

| Field | Value |
|-------|-------|
| Name | Databricks-to-Databricks (D2D) Sharing |
| Description | Different metastores but both Databricks — uses Delta Sharing with native catalog integration. |
| Complexity | Medium |
| Latency | Near zero (metadata auto-sync, live reads via pre-signed URLs) |
| Cost | S3 egress if cross-region, zero compute for sharing |

Substitute `<consumer_slug>`, `<consumer_name>`, `<tables>` from inputs.

## Implementation Steps
1. Get consumer metastore sharing identifier (consumer runs: `SELECT current_metastore()`)
2. Provider: `CREATE SHARE sales_share`
3. Provider: `ALTER SHARE sales_share ADD TABLE demo_sales.<tables>`
4. Provider: `CREATE RECIPIENT <consumer_slug> USING ID '<consumer-sharing-id>'`
5. Provider: `GRANT SELECT ON SHARE sales_share TO RECIPIENT <consumer_slug>`
6. Consumer: `CREATE PROVIDER sales_provider USING ID '<provider-sharing-id>'`
7. Consumer: `CREATE CATALOG sales_shared USING SHARE sales_provider.sales_share`
8. Consumer: `GRANT USE CATALOG ON sales_shared TO their local groups`
9. Consumer: query via `SELECT * FROM sales_shared.gold_products.*`

## Generated SQL
```sql
-- PROVIDER SIDE
CREATE SHARE IF NOT EXISTS <consumer_slug>_share
COMMENT 'Data products shared with <consumer_name>';

ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.revenue_dashboard;
ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.customer_segments;
ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.product_catalog_public;

CREATE RECIPIENT IF NOT EXISTS <consumer_slug>
  USING ID '<CONSUMER_METASTORE_SHARING_ID>'
  COMMENT '<consumer_name> workspace';

GRANT SELECT ON SHARE <consumer_slug>_share TO RECIPIENT <consumer_slug>;
SHOW ALL IN SHARE <consumer_slug>_share;

-- CONSUMER SIDE
SELECT current_metastore() AS my_sharing_id;

CREATE PROVIDER IF NOT EXISTS sales_data_provider
  USING ID '<PROVIDER_METASTORE_SHARING_ID>'
  COMMENT 'Sales domain data provider';

SHOW SHARES IN PROVIDER sales_data_provider;

CREATE CATALOG IF NOT EXISTS sales_shared
  USING SHARE sales_data_provider.<consumer_slug>_share;

SELECT * FROM sales_shared.gold_products.revenue_dashboard LIMIT 10;

GRANT USE CATALOG ON CATALOG sales_shared TO `<consumer_slug>`;
GRANT SELECT ON CATALOG sales_shared TO `<consumer_slug>`;
```

## Architecture Diagram
```
┌───────────────────────────┐           ┌───────────────────────────┐
│  PROVIDER WORKSPACE       │  Delta    │  CONSUMER WORKSPACE       │
│  Metastore A              │  Sharing  │  Metastore B              │
│  demo_sales.gold_products │──────────►│  sales_shared (CATALOG)   │
│  S3: s3://provider-bucket │◄──────────│  Reads via pre-signed URLs│
└───────────────────────────┘  direct   └───────────────────────────┘
  Auth: Metastore-to-metastore (automatic)  Cost: S3 egress if cross-region
```

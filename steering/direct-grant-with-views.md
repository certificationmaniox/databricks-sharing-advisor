# Solution: DIRECT_GRANT_WITH_VIEWS

**Read this when** Decision 1 selects `DIRECT_GRANT_WITH_VIEWS` (i.e. `same_metastore` == "Yes"
and not read-write). Secondary: Cross-Catalog Views.

| Field | Value |
|-------|-------|
| Name | Direct GRANT + Cross-Catalog Views |
| Description | Same metastore — grant SELECT directly and consumer creates views in their catalog. |
| Complexity | Low |
| Latency | Zero (live read from same Delta tables) |
| Cost | Zero additional (same S3, same region) |

Substitute `<consumer_slug>`, `<consumer_name>`, `<tables>` from inputs. `<schema>` = the part
of `tables_to_share` before the first `.` (fallback `gold_products`).

## Implementation Steps
1. Create account-level group for `<consumer_name>`
2. `GRANT USE CATALOG ON CATALOG demo_sales TO \`<consumer_slug>\``
3. `GRANT USE SCHEMA ON SCHEMA demo_sales.<schema> TO \`<consumer_slug>\``
4. `GRANT SELECT ON TABLE/SCHEMA demo_sales.<tables> TO \`<consumer_slug>\``
5. Consumer creates views in their catalog referencing demo_sales tables
6. Document in table comments + add tags
7. Set up audit monitoring

## Generated SQL
```sql
-- PROVIDER SIDE (run in provider workspace)
GRANT USE CATALOG ON CATALOG demo_sales TO `<consumer_slug>`;
GRANT USE SCHEMA ON SCHEMA demo_sales.<schema> TO `<consumer_slug>`;
GRANT SELECT ON SCHEMA demo_sales.<schema> TO `<consumer_slug>`;

-- CONSUMER SIDE (run in consumer workspace)
CREATE CATALOG IF NOT EXISTS <consumer_slug>_catalog;
CREATE SCHEMA IF NOT EXISTS <consumer_slug>_catalog.shared_products;

CREATE OR REPLACE VIEW <consumer_slug>_catalog.shared_products.revenue
AS SELECT * FROM demo_sales.gold_products.revenue_dashboard;

CREATE OR REPLACE VIEW <consumer_slug>_catalog.shared_products.customers
AS SELECT * FROM demo_sales.gold_products.customer_segments;

SELECT * FROM <consumer_slug>_catalog.shared_products.revenue LIMIT 5;
```

## Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                    SAME METASTORE                                 │
│  ┌──────────────────┐         ┌──────────────────────────────┐  │
│  │  demo_sales      │  GRANT  │  <consumer_slug>_catalog     │  │
│  │  gold_products   │────────►│  shared_products (VIEWS)     │  │
│  │  (Delta tables)  │ SELECT  │  → revenue, customers, etc.  │  │
│  └──────────────────┘         └──────────────────────────────┘  │
│  Data: Same S3, same region, zero copy, zero latency             │
│  Auth: GRANT to account-level group   Cost: Zero additional      │
└─────────────────────────────────────────────────────────────────┘
```

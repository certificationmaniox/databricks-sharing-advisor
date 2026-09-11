# Consumer Intake (You Are Bringing Data In)

**Read this when** `direction` == "Consumer (bring in)" — Decision 0.5 routes here instead of the
producer tree. Selects among the five consumer solutions in Decision 1-C.

The consumer's default is **query in place, not copy in**. D2D shares, Lakehouse Federation, and
external-location reads all leave the data where it lives. Introduce a copy-based ingestion
pipeline only when you need historical snapshots or query volume makes live federation too chatty.

| `source_platform` | Solution | Why |
|-------------------|----------|-----|
| Another Databricks account/metastore | `CONSUME_D2D_SHARE` | Mount the share as a catalog; data stays in the provider's S3, query live; provider masks enforced |
| Query engine (Snowflake/Postgres/Redshift/MySQL/BigQuery) | `LAKEHOUSE_FEDERATION` | Foreign catalog over a CONNECTION; push queries down — no ingestion pipeline |
| Another catalog (AWS Glue / Hive Metastore) | `CATALOG_FEDERATION` | Federate the whole metastore into UC; one three-level namespace, governed identically |
| Partner S3 bucket (Delta/Parquet) | `EXTERNAL_LOCATION_READ` | Read-only cross-account IAM role + external location; read in place |
| Open Delta Sharing provider | `CONSUME_OPEN_DELTA_SHARING` | Point `delta-sharing`/Spark at the `.share` profile; works even if the vendor isn't on Databricks |

## CONSUME_D2D_SHARE — mount another Databricks share
```sql
-- CONSUMER
SELECT current_metastore() AS my_sharing_id; -- send to the provider
CREATE PROVIDER IF NOT EXISTS demo_provider USING ID '<PROVIDER_METASTORE_SHARING_ID>';
CREATE CATALOG IF NOT EXISTS sales_shared USING SHARE demo_provider.finance_share;
SELECT * FROM sales_shared.gold_products.revenue_dashboard LIMIT 10;
```
Provider masks/row filters are enforced (unlike open-protocol or DEEP CLONE). Cross-region = S3 egress.

## LAKEHOUSE_FEDERATION — query a source engine live
```sql
-- CONSUMER (Databricks)
CREATE CONNECTION partner_snowflake TYPE snowflake OPTIONS (
  host 'partner_account.snowflakecomputing.com', port '443',
  user secret('partner','sf_user'), password secret('partner','sf_password'));
CREATE FOREIGN CATALOG partner_sales USING CONNECTION partner_snowflake
  OPTIONS (database 'SALES_DB');
SELECT o.order_id, o.amount, g.margin
  FROM partner_sales.public.orders o
  JOIN demo_sales.gold_products.product_catalog_public g USING (product_id);
```
Queries push down to the source — no copy into your S3. Materialize locally only if it gets chatty.

## CATALOG_FEDERATION — federate a Glue/Hive metastore
```sql
-- Setup once (SQL)
CREATE CONNECTION glue_conn TYPE glue OPTIONS (
  aws_region 'us-east-1', aws_account_id '<glue-account-id>',
  credential '<uc-service-credential-id>');
CREATE FOREIGN CATALOG glue_federated USING CONNECTION glue_conn
  OPTIONS (storage_root 's3://demo-glue-backed/');
```
```python
# CONSUMER — read via the three-level namespace
df = spark.read.table("glue_federated.curated_sales.fct_order_line")
```
UC routes and governs Glue-backed S3 and UC-managed tables identically through one namespace.

## EXTERNAL_LOCATION_READ — read a partner's S3 bucket
```sql
-- CONSUMER
CREATE STORAGE CREDENTIAL partner_read_cred
  WITH (AWS_IAM_ROLE = 'arn:aws:iam::PARTNER_ACCOUNT:role/read-role');
CREATE EXTERNAL LOCATION partner_feed
  URL 's3://partner-feed/demo-exports/' WITH (STORAGE CREDENTIAL partner_read_cred);
CREATE TABLE bronze.partner_orders
  USING DELTA LOCATION 's3://partner-feed/demo-exports/orders';
```
Read-in-place = no duplicate storage; use `COPY INTO` instead only for an isolated local snapshot.

## CONSUME_OPEN_DELTA_SHARING — subscribe to an open feed
```python
# CONSUMER (Databricks)
PROFILE = "/Volumes/main/secure/config.share"
df = spark.read.format('deltaSharing').load(f"{PROFILE}#vendor_share.gold.metrics")
df.write.mode('overwrite').saveAsTable('bronze.vendor_metrics')  # persist only if you must keep it
```
Works even if the vendor is not on Databricks.

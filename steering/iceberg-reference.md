# Unity Catalog + Apache Iceberg Reference

**Read this when** the scenario involves Iceberg (`table_format` is any Iceberg/UniForm option,
or the consumer is an Iceberg REST client), or the user asks about UC's Iceberg capabilities.

Source: Databricks blog, "Advancing Apache Iceberg on Databricks: Iceberg v3 GA, Open Sharing,
and Unified Governance"
(https://www.databricks.com/blog/unity-catalog-and-next-era-apache-icebergtm). Content was
rephrased for compliance with licensing restrictions.

The catalog — not just the table format — determines whether open data can be governed,
optimized, and shared consistently across engines. UC positions itself as an interoperable
Iceberg catalog across five capability areas:

1. **Open APIs + credential vending** — Managed Iceberg is GA: create/read/write Iceberg tables
   in UC from any engine (Spark, Trino, Flink, Snowflake, DuckDB, pandas) via UC's Iceberg REST
   Catalog API, without copying data or granting broad storage permissions. UC also vends
   credentials for federated (foreign) Iceberg tables. Iceberg-compatible materialized views
   are in gated preview (`CREATE MATERIALIZED VIEW ... USING ICEBERG`).
2. **Catalog federation** — Foreign Iceberg is GA: UC can govern Iceberg tables managed in other
   catalogs (AWS Glue, Snowflake Horizon, Hive Metastore, Google Cloud Lakehouse, Palantir,
   Salesforce, Workday) while data and source catalog stay in place — a single pane of glass.
3. **Cross-engine ABAC (Beta)** — Define column masks, row filters, and tag-based policies once
   in UC. When an external Iceberg engine requests access, UC evaluates policies during
   server-side scan planning and returns a filtered scan plan, so engines only read authorized
   data. Any client implementing Iceberg REST scan planning (Iceberg 1.11+) enforces this.
4. **Zero-copy secure sharing** — Iceberg is a first-class source and destination in Delta
   Sharing. Sharing to Iceberg REST clients is GA; recipients (Snowflake, Trino, Flink, Spark)
   query shared data live with no manual ingestion. Foreign Iceberg sharing is in Public Preview.
5. **Performance/format innovation** — Predictive Optimization + Liquid Clustering keep tables
   fast without manual tuning, and layout improvements benefit external engines too. Iceberg v3
   is GA (deletion vectors, row tracking, VARIANT) across managed, foreign, and UniForm tables;
   these work across both Delta and Iceberg without rewriting data. Iceberg v4 (adaptive metadata
   tree) is the next step, with Delta 5.0 proposed to adopt the same structure.

When to lean on Iceberg in this advisor:
- Consumer runs a non-Databricks Iceberg engine → `ICEBERG_REST_SHARING`.
- Data lives in an external catalog you don't want to migrate → register as Foreign Iceberg and
  share in place.
- Multiple external engines hit the same table with row/column security needs → use ABAC rather
  than per-engine views.

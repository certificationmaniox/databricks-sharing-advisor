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
   in UC. When an external Iceberg engine queries UC directly, UC evaluates policies during
   server-side scan planning and returns a filtered scan plan, so engines only read authorized
   data. Any client implementing Iceberg REST scan planning (Iceberg 1.11+) enforces this. This
   governs *direct query access*, not what a Delta Sharing recipient sees — see area 4.
4. **Zero-copy secure sharing** — Iceberg is a first-class source and destination in Delta
   Sharing. Sharing to Iceberg REST clients is GA; recipients (Snowflake, Trino, Flink, Spark)
   query shared data live with no manual ingestion. Foreign Iceberg sharing is in Public Preview.
   ABAC and sharing interact carefully: a provider can add ABAC-secured tables/schemas to a
   share, but the policy does NOT govern the recipient — the recipient gets full access to the
   shared asset and applies their own ABAC. To restrict what an external recipient sees, share an
   aggregated Materialized View, a secure/filtered view, or only specific partitions.
5. **Performance/format innovation** — Predictive Optimization + Liquid Clustering keep tables
   fast without manual tuning, and layout improvements benefit external engines too. Iceberg v3
   is GA (deletion vectors, row tracking, VARIANT) across managed, foreign, and UniForm tables;
   these work across both Delta and Iceberg without rewriting data. Iceberg v4 (adaptive metadata
   tree) is the next step, with Delta 5.0 proposed to adopt the same structure.

When to lean on Iceberg in this advisor:
- Consumer runs a non-Databricks Iceberg engine → `ICEBERG_REST_SHARING`.
- Data lives in an external catalog you don't want to migrate → register as Foreign Iceberg and
  share in place.
- Multiple external engines query the same UC table directly with row/column security needs →
  use ABAC rather than per-engine views (remembering ABAC does not restrict a share recipient).

## Apache Iceberg v3 (GA) — what to share and why

**Read this for Decision 1c** (the table-format modifier). Iceberg v3 is GA on Unity Catalog
managed, foreign, and UniForm-enabled tables. Source: Databricks, "The next era of the open
lakehouse: Apache Iceberg™ v3"
(https://www.databricks.com/blog/next-era-open-lakehouse-apache-icebergtm-v3-public-preview-databricks)
and the Iceberg v3 GA blog above. Content was rephrased for compliance with licensing restrictions.

v3 features and why they matter for sharing:

| Feature | What it does | When to recommend |
|---------|--------------|-------------------|
| **Row lineage** | Every row carries a permanent row ID + a sequence number marking when it last changed, so consumers identify changed rows without full scans. | Cross-engine CDC to a non-Databricks consumer. |
| **Deletion vectors** | Logical deletes tracked in lightweight delete files instead of rewriting Parquet — much faster change application than copy-on-write. | Same CDC/incremental case; high-update tables. |
| **VARIANT** | Native semi-structured column type; store logs/API/clickstream/IoT payloads beside relational columns in one table, queryable with standard SQL, no schema migration when new fields appear. | Semi-structured or schema-flexible data. |
| **UniForm + v3** | Write once to Delta, read as Iceberg from Snowflake/BigQuery/Redshift/Athena/Trino — now without giving up Delta's performance features (v3 features surface on the Iceberg read). | Delta source + Iceberg-reading consumer. |

Decision 1c mapping (refines the shared table's *format*, not the primary solution):
- `needs_cdc` == "Yes" AND consumer is non-Databricks → **managed Iceberg v3** (row lineage +
  deletion vectors). Stronger than Delta `WITH HISTORY`, which the consumer's engine must
  understand. For a Databricks-to-Databricks consumer, Delta change data feed is fine.
- Semi-structured data → **managed Iceberg v3 with VARIANT** (ship the payload in one governed
  table instead of flattening or dumping to strings).
- `table_format` == "Delta" AND consumer reads Iceberg (Snowflake / Trino / BigQuery / Redshift /
  Athena / Iceberg REST client) → **UniForm** (single Delta copy, no replication pipeline).

Enablement note: managed Iceberg v3 requires Databricks Runtime 18.0+ with Unity Catalog. Treat
this as a format recommendation on the shared object — the `ALTER SHARE ... ADD TABLE` mechanics
are unchanged.

Looking ahead: **Iceberg v4** (adaptive metadata tree — most operations write a single metadata
file, relative-path support, modernized statistics for VARIANT/GEOMETRY) is the next step, with
Delta 5.0 proposed to adopt the same structure. Not GA; mention only as roadmap.

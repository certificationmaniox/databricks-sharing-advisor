---
name: "databricks-sharing-advisor"
displayName: "Databricks Sharing Architecture Advisor"
description: "Recommends the best Databricks data-sharing architecture (Delta Sharing, Direct Grant, Iceberg REST, JDBC/ODBC SQL warehouse, or shared external location) for a given scenario by asking discovery questions and applying a decision tree. First picks the collaboration modality — direct table sharing, Clean Rooms, Marketplace, or AI-asset/OpenSharing — then produces prerequisites, security measures, cost considerations, implementation steps, and ready-to-run SQL/code, and can publish recommendations to Confluence via the Atlassian MCP. Covers both directions (producer sharing out and consumer bringing data in via federation / external location / open sharing), same/different metastore, cross-account, cross-region, Iceberg v3 / UniForm format choices, an escalation ladder, troubleshooting, and Databricks/Snowflake/Power BI/Python/Spark/Iceberg/JDBC/REST-API consumers."
keywords: ["databricks", "delta-sharing", "unity-catalog", "apache-iceberg", "jdbc", "confluence"]
author: "maniox"
source: "https://github.com/certificationmaniox/databricks-sharing-advisor"
repository: "https://github.com/certificationmaniox/databricks-sharing-advisor"
---

# Databricks Sharing Architecture Advisor

## Overview

This power helps you choose the right architecture for sharing Databricks data with a
consumer. Given a scenario (metastore/account/region topology, consumer platform, identity,
data characteristics, freshness, security, and compliance needs), it applies a deterministic
decision tree to recommend a primary and secondary solution, then produces the prerequisites,
security measures, cost considerations, step-by-step implementation, generated SQL/code, and
an architecture diagram.

It is a knowledge-base power: the recommendation is reasoning over documented rules, not code
execution. Ask for a recommendation in natural language (or provide the inputs directly) and
the assistant walks the decision tree below to produce the same output the original advisor
notebook would.

> **Recent context (2025–2026):** Delta Sharing is evolving into **OpenSharing**, now a Linux
> Foundation project and a vendor-neutral protocol that extends zero-copy sharing beyond tables
> to AI assets (models, agents, unstructured data) and adds cross-cloud connectivity. Sharing
> live Materialized Views and Streaming Tables is GA, and **Apache Iceberg v3 is GA** on Unity
> Catalog (deletion vectors, row lineage, VARIANT) across managed, foreign, and UniForm tables.
> This advisor picks the **collaboration modality first** (Decision 0: direct table sharing,
> Clean Rooms, Marketplace, or AI-asset sharing) before the table-sharing decision tree, and
> factors Iceberg v3 / UniForm into the shared table format (Decision 1c). See the "Recent
> Sharing Features (2025–2026)" reference section near the end of this file for details and sources.

## How to Use

1. Provide the scenario. Either answer the Discovery Questions below or describe your setup in
   prose (e.g. "different metastore, consumer is on Snowflake, read-only, no PII").
2. The assistant applies the Decision Tree to pick the primary and secondary solution.
3. The assistant produces: solution summary, prerequisites, security measures, warnings, cost
   considerations, implementation steps, generated SQL/code, and an architecture diagram.
4. Any input not provided uses the default listed below.

### Sample Prompt (for the best result)

**Show this to the user first.** When the power is started with no scenario (e.g. "help me get
started", "try this power", or an empty/vague request), the assistant's FIRST reply must display
the full sample prompt template below so the user knows exactly what to send. Present it, invite
them to copy and fill in the bracketed values, and tell them they can instead answer one question
at a time. Only begin the interactive intake or a recommendation after they respond.

Copy, edit the bracketed values, and send. Providing the topology, consumer platform, access
type, and data sensitivity up front lets the advisor skip intake and return a complete
recommendation in one pass:

> Recommend a Databricks data-sharing architecture. Provider and consumer are in
> [different / the same] metastore, [different / the same] Databricks account, and
> [different / the same] AWS region ([provider region] → [consumer region]). The consumer is
> [consumer name/team] on [Databricks / Snowflake / Power BI / Python/Pandas / Spark (non-Databricks) /
> dbt / an Iceberg REST client / a JDBC-ODBC SQL client]. Access is [read-only / read-write].
> Tables to share: [catalog.schema.table or catalog.schema.*] in [Delta / Iceberg / UniForm] format.
> Data is [Public / Internal / Confidential / Restricted] and [contains / does not contain] PII;
> freshness needed is [real-time / near real-time / hourly / daily / weekly]. Give me the primary
> and secondary solution, prerequisites, security measures, cost considerations, implementation
> steps, generated SQL, and an architecture diagram.

Minimal version when you want the advisor to ask for anything missing:

> Help me choose how to share [catalog.schema.*] with [consumer team] on [platform],
> [read-only/read-write]. Ask me anything you need.

### Interactive Intake (default when the scenario is vague)

If the user has NOT already described their setup in enough detail, walk them through the
Discovery Questions interactively instead of assuming everything. Rules:

- **Ask ONE question at a time.** Do NOT present questions in groups or dump the whole list. Ask a
  single question, show its options and its default, and note the user can skip. Only after the
  user replies do you ask the next question. Follow the producer-first order below, skipping any
  question that is already known or made irrelevant by an earlier answer:
  1. `shared_asset_kind` → 2. `collaboration_intent` → 3. `raw_data_exposure_ok` (only if
     `collaboration_intent` is "Joint analysis..." or unclear) → 4. `recipient_count` →
  5. `tables_to_share` → 6. `provider_asset_type` → 7. `same_metastore` → 8. `same_account` →
  9. `same_region` → 10. `provider_region` → 11. `table_format` → 12. `foreign_catalog` (only if
     `table_format` is foreign Iceberg) → 13. `consumer_name` → 14. `consumer_asset_intent` →
  15. `consumer_platform` → 16. `connectivity` → 17. `consumer_region` → 18. `consumer_identity` →
  19. `consumer_external` → 20. `consumer_needs_transform` → 21. `access_type` → 22. `contains_pii` →
  23. `data_classification` → 24. `needs_column_security` → 25. `needs_row_security` →
  26. `groups_exist` → 27. `data_volume` → 28. `needs_cdc` → 29. `freshness_requirement` →
  30. `sharing_duration` → 31. `data_residency`.
  The first four questions establish the collaboration modality (Decision 0). If they resolve to
  a non-table-sharing modality (Clean Rooms, Marketplace, or AI-asset sharing), skip the
  table-sharing-only questions that no longer apply and go to the matching Decision 0 branch.
- **Keep the console clean during intake.** Do NOT print the activated POWER.md, the decision
  tree, solution catalog, or long examples while asking questions. Just ask the current question.
  Save the full recommendation for the end.
- **Unity Catalog naming.** For `tables_to_share`, ask for the fully-qualified Unity Catalog path
  in `catalog.schema.table` form (or `catalog.schema.*` for a whole schema). UC names are always
  three levels: catalog, schema, table.
- **Data-product framing (`provider_asset_type` / `consumer_asset_intent`).** These describe the
  data-mesh nature of what is shared, on the provider side and how the consumer expects to use it.
  They do NOT change which primary solution Decision 1 selects (that stays driven by topology,
  platform, and access type), but they refine the recommendation:
  - `consumer_asset_intent` == "Same as provider" (default) inherits `provider_asset_type`.
  - "Curated/aggregate data product" → prefer sharing a **Materialized View** (Decision 1b) so the
    consumer gets published aggregates, not raw rows; note column mapping to rename/hide columns.
  - "Source-aligned data product" → share the underlying tables (or a Streaming Table if freshness
    is real-time/near real-time per Decision 1b); expect the consumer to build their own curated
    layer on top.
  - "Data port" → treat as a published, contract-bound interface: prefer sharing stable views or
    an MV over the physical tables, and call out that the shared object is the port's contract.
  - "Tables" (default) → share the physical tables as-is (unchanged behavior).
  Recap both values in the Input Summary, and mention in the recommendation how the asset type
  shaped the chosen `shared_object`.
- **Wait for the user's input after each question. Do NOT answer your own questions or assume
  responses.** After asking a question, STOP and let the user reply before asking the next one or
  producing the recommendation. Never fabricate, simulate, or pre-fill the user's answers, and
  never run ahead through later questions on your own.
- **Apply defaults only on explicit skip.** Use a question's default from the Discovery Questions
  table only when the user actually skips it — i.e. they say "skip", "default", "don't know", or
  answer the group while leaving that field unmentioned. Absence of a reply is NOT a skip; keep
  waiting until the user responds. The user may also say "use all defaults" to accept every
  remaining default at once and jump to the recommendation.
- **Don't re-ask what's known.** Skip any question the user already answered in their prose, and
  skip questions made irrelevant by earlier answers (e.g. don't ask `foreign_catalog` unless
  `table_format` is foreign Iceberg).
- **Skip intake when the scenario is already specific.** If the user gave a full prose scenario or
  explicitly asks for a direct answer, go straight to the recommendation using prose + defaults —
  do not force the walkthrough.
- **Always recap.** Before or with the recommendation, show the Input Summary (step 8 of Output
  Format) listing every value used and which were defaults, so the user can correct any.

5. Optionally, publish the recommendation to Confluence or pull existing sharing docs for context using the Atlassian Confluence MCP (see below).

## Confluence Integration (Atlassian MCP)

This power ships an `mcp.json` for the Atlassian Confluence MCP server
(`@aashari/mcp-server-atlassian-confluence`). Use it to:
- **Publish** a generated recommendation as a Confluence page (e.g. a "Data Sharing Design"
  space) so the advisor's output becomes durable team documentation.
- **Look up** existing sharing/governance runbooks or standards in Confluence and factor them
  into the recommendation before answering.
- **Search** for prior recommendations for the same consumer to keep decisions consistent.

**Typical MCP tools** exposed by this server (exact names surface at runtime after the server
is enabled — use the ones listed there): list/search Confluence spaces, list/search/get pages,
and create/update a page. Common flows:
- Find a space, then search pages for the consumer name to reuse a prior design.
- After producing a recommendation, create a page whose body is the recommendation output
  (solution summary, prerequisites, security, cost, implementation steps, SQL, diagram).

**Suggested workflow when the user asks to "document this in Confluence":**
1. Confirm the target space (ask, or search spaces if not given).
2. Generate the recommendation using the decision tree.
3. Create a Confluence page titled `Data Sharing Design - <consumer_name>` with the
   recommendation as the body; report the page URL back to the user.

## Discovery Questions (Inputs)

| Key | Question | Options | Default |
|-----|----------|---------|---------|
| `same_metastore` | Same metastore? | Yes, No | No |
| `same_account` | Same Databricks account? | Yes, No | Yes |
| `same_region` | Same AWS region? | Yes, No | Yes |
| `consumer_platform` | Consumer platform? | Databricks, Snowflake, Power BI, Python/Pandas, Spark (non-Databricks), dbt, Iceberg REST client (Trino/Flink/DuckDB/etc.), JDBC/ODBC SQL client (BI/app/dbt), Other | Databricks |
| `connectivity` | Preferred connectivity? | Any (let advisor choose), Data-copy/share protocol, Live SQL endpoint (JDBC/ODBC) | Any (let advisor choose) |
| `table_format` | Source/shared table format? | Delta, Iceberg (managed), Iceberg (foreign/external catalog), UniForm | Delta |
| `foreign_catalog` | If foreign Iceberg, which catalog? | N/A, AWS Glue, Snowflake Horizon, Hive Metastore, Google Cloud Lakehouse, Palantir, Salesforce, Workday | N/A |
| `provider_region` | Provider AWS region | free text | us-east-1 |
| `consumer_region` | Consumer AWS region | free text | us-east-1 |
| `consumer_identity` | Consumer identity type? | Human Users, Service Principal, External Application, Partner Organization | Service Principal |
| `access_type` | Access type needed? | Read-only, Read-write | Read-only |
| `groups_exist` | Account-level groups exist? | Yes, No | No |
| `data_volume` | Data volume? | Small (< 1 GB), Medium (1-100 GB), Large (100 GB - 1 TB), Very Large (> 1 TB) | Medium (1-100 GB) |
| `contains_pii` | Contains PII? | Yes, No | No |
| `data_classification` | Data classification? | Public, Internal, Confidential, Restricted | Internal |
| `needs_cdc` | Needs Change Data Feed (CDC)? | Yes, No | No |
| `freshness_requirement` | Freshness requirement? | Real-time (< 1 min), Near real-time (< 15 min), Hourly, Daily, Weekly | Daily |
| `sharing_duration` | Sharing duration? | One-time export, Ongoing (continuous), Time-limited (project) | Ongoing |
| `data_residency` | Data residency requirement? | No restriction, Must stay in same region, Must stay in same country, Must stay in same account | No restriction |
| `needs_column_security` | Column-level security? | Yes, No | No |
| `needs_row_security` | Row-level security? | Yes, No | No |
| `consumer_external` | Consumer external to org? | Yes, No | No |
| `consumer_needs_transform` | Consumer needs transformation? | No (read-only queries), Yes (build views/tables on top), Yes (ML/AI workloads) | No (read-only queries) |
| `tables_to_share` | Tables to share (Unity Catalog `catalog.schema.table`, or `catalog.schema.*` for a whole schema) | free text | demo_sales.gold_products.* |
| `provider_asset_type` | What is the provider sharing? | Source-aligned data product, Curated/aggregate data product, Data port, Tables | Tables |
| `consumer_name` | Consumer name/team | free text | Finance Team |
| `consumer_asset_intent` | What does the consumer consume it as? | Source-aligned data product, Curated/aggregate data product, Data port, Tables, Same as provider | Same as provider |
| `direction` | Are you sharing data OUT or bringing data IN? | Producer (share out), Consumer (bring in) | Producer (share out) |
| `source_platform` | If Consumer, where is the data coming from? | Another Databricks account/metastore, Query engine (Snowflake/Postgres/Redshift/MySQL/BigQuery), Another catalog (AWS Glue / Hive Metastore), Partner S3 bucket (Delta/Parquet files), Open Delta Sharing provider | Query engine (Snowflake/Postgres/Redshift/MySQL/BigQuery) |
| `shared_asset_kind` | What kind of asset is shared? | Data (tables/views), AI model, Agent / Agent Skill, Unstructured files, Notebook/dashboard | Data (tables/views) |
| `collaboration_intent` | How do you want to collaborate? | Direct share to a known consumer, Joint analysis without exposing raw data, Publish to many/unknown consumers, Let advisor choose | Let advisor choose |
| `recipient_count` | How many recipients? | One / a few named, Many / broad audience | One / a few named |
| `raw_data_exposure_ok` | OK to expose raw rows to the other party? | Yes, No (compute on joined data only) | Yes |

`consumer_slug` = `consumer_name` lowercased with spaces and hyphens replaced by underscores.

## Decision Tree

### Decision 0: Collaboration modality (evaluate first)

Pick the sharing *modality* before the table-sharing decision tree. Evaluate in order; first
match wins. Only if the result is `TABLE_SHARING` do you continue to Decision 1. The other
modalities are first-class Databricks collaboration approaches that Decision 1 does not model.

1. If `shared_asset_kind` in {"AI model", "Agent / Agent Skill", "Unstructured files"} OR
   `collaboration_intent` implies sharing models/agents:
   - modality = `AI_ASSET_SHARING`
   - note: "OpenSharing (the evolution of Delta Sharing, now a Linux Foundation project) shares
     AI assets — models, agents/Agent Skills, and unstructured files — zero-copy over the open
     protocol. For conversational/natural-language access to data, use **Genie Agent Sharing
     (Beta)** rather than sharing raw tables."
   - Then still run Decision 1 for any accompanying tabular data the asset depends on.
2. Else if `raw_data_exposure_ok` == "No (compute on joined data only)" OR `collaboration_intent`
   == "Joint analysis without exposing raw data":
   - modality = `CLEAN_ROOMS`
   - note: "Use **Databricks Clean Rooms** (powered by Delta Sharing) for privacy-centric
     collaboration where neither party exposes raw data. Supports multi-party rooms (up to 10
     orgs), any cloud (GA on AWS/Azure/GCP), in-place privacy-centric identity resolution, and
     self-run notebooks with explicit approval."
   - Strongly prefer this over table sharing when `contains_pii` == "Yes" AND
     `consumer_external` == "Yes" — it replaces the "don't share PII externally" dead-end with a
     workable path.
3. Else if `collaboration_intent` == "Publish to many/unknown consumers" OR `recipient_count`
   == "Many / broad audience":
   - modality = `MARKETPLACE`
   - note: "Use the **Databricks Marketplace** to publish a data (or AI-asset) product to many
     or unknown consumers via Delta Sharing — recipients get live, no-copy access. Choose this
     over a per-recipient RECIPIENT when the audience is broad or you want a listing/monetization
     path. For a small set of named recipients, use table sharing (Decision 1)."
4. Else:
   - modality = `TABLE_SHARING` → continue to Decision 1.

Emit the chosen modality in the recommendation. For `CLEAN_ROOMS`, `MARKETPLACE`, and
`AI_ASSET_SHARING`, present the modality note as the primary recommendation and use Decision 1
only for any supporting tabular data; the Decision 1 catalog/SQL/diagram apply to that tabular
portion.

### Decision 0.5: Direction (producer vs consumer)

The most useful cut after modality: are you the **producer** (sharing data out to consumers
wherever they run) or the **consumer** (bringing external data into your own lakehouse)? The two
use different toolkits. Evaluate this before Decision 1.

- If `direction` == "Producer (share out)" (default) → continue to **Decision 1** (producer
  protocol tree below).
- If `direction` == "Consumer (bring in)" → use **Decision 1-C** (consumer intake tree) instead
  of Decision 1. The consumer's default is "query in place," not "copy in": prefer a live,
  zero-copy read and only introduce a copy-based ingestion pipeline when you need historical
  snapshots or query volume makes live federation too chatty.

#### Decision 1-C: Consumer intake (you are bringing data in)

Evaluate in order; first match wins. Selects `primary` from the consumer solutions.

1. If `source_platform` == "Another Databricks account/metastore":
   - primary = `CONSUME_D2D_SHARE`, secondary = "Open Delta Sharing client"
   - note: "Mount the provider's Delta share as a catalog (`CREATE CATALOG ... USING SHARE`); the
     data stays in the provider's S3 and you query it live. Masks/row filters defined by the
     provider are enforced (unlike open-protocol or DEEP CLONE)."
2. Else if `source_platform` == "Query engine (Snowflake/Postgres/Redshift/MySQL/BigQuery)":
   - primary = `LAKEHOUSE_FEDERATION`, secondary = "Copy-based ingestion (only if too chatty)"
   - note: "Register the source as a foreign catalog over a JDBC-style CONNECTION and push queries
     down to it — query in place, no ingestion pipeline. Compute is paid by the source engine."
3. Else if `source_platform` == "Another catalog (AWS Glue / Hive Metastore)":
   - primary = `CATALOG_FEDERATION`, secondary = "Lakehouse Federation"
   - note: "Federate the whole metastore into UC as a foreign catalog; read every registered
     table through one three-level `catalog.schema.table` namespace, governed identically. The
     common AWS case is a Glue-backed 'unified layer' mixing native UC Delta and Glue S3 tables."
4. Else if `source_platform` == "Partner S3 bucket (Delta/Parquet files)":
   - primary = `EXTERNAL_LOCATION_READ`, secondary = "COPY INTO (for an isolated local snapshot)"
   - note: "Register the partner's path in UC with a read-only cross-account IAM role via a
     storage credential + external location, then read in place. No duplicate storage."
5. Else (`source_platform` == "Open Delta Sharing provider"):
   - primary = `CONSUME_OPEN_DELTA_SHARING`, secondary = "Persist to bronze (only if you must keep it)"
   - note: "Point Spark or the `delta-sharing` client at the provider's `.share` profile. Works
     even if the provider is not on Databricks. Persist into bronze only if you need to retain it."

For a consumer recommendation, skip the producer-only Decisions 1, 1b, and 1c, and skip
producer prerequisites/SQL; use the consumer solution's steps and code instead. Decisions 3
(security) and 4 (cost) still apply where relevant (e.g. cross-region egress on federated reads).

### Decision 1: Primary + secondary solution

**(Producer direction only.)** Evaluate in order; first match wins.

1. If `access_type` == "Read-write":
   - primary = `SHARED_EXTERNAL_LOCATION`, secondary = "Reverse ETL Pipeline"
   - warning: "Delta Sharing is READ-ONLY. For write access, use shared S3 external locations with IAM roles."
   - Iceberg note: Managed Iceberg on Unity Catalog is read-write from any engine via the UC Iceberg REST Catalog API — if both sides can speak Iceberg REST, prefer `ICEBERG_REST_SHARING` (below) over a raw shared S3 location for governed writes.
2. Else if `same_metastore` == "Yes":
   - primary = `DIRECT_GRANT_WITH_VIEWS`, secondary = "Cross-Catalog Views"
3. Else if `consumer_platform` == "JDBC/ODBC SQL client (BI/app/dbt)" OR `connectivity` == "Live SQL endpoint (JDBC/ODBC)":
   - primary = `JDBC_SQL_WAREHOUSE`, secondary = "Delta Sharing (Open Protocol)"
   - note: The consumer connects live to a Databricks SQL warehouse over JDBC/ODBC. Governance (UC grants, dynamic views, ABAC) applies at query time; no data copy leaves Databricks. Best when the consumer is a BI tool, app, or dbt that speaks SQL and needs live, governed reads rather than a shared dataset copy.
   - If `access_type` == "Read-write": warning: "JDBC to a SQL warehouse is effectively read for external consumers; writes require table ACLs the consumer usually won't have. For true read-write use SHARED_EXTERNAL_LOCATION or managed Iceberg."
4. Else if `consumer_platform` == "Iceberg REST client (Trino/Flink/DuckDB/etc.)" OR `table_format` in {"Iceberg (managed)", "Iceberg (foreign/external catalog)", "UniForm"}:
   - primary = `ICEBERG_REST_SHARING`, secondary = "Delta Sharing (Open Protocol)"
   - If `table_format` == "Iceberg (foreign/external catalog)" → note: "Foreign Iceberg sharing (Public Preview): register the external table in UC and share it in place; data and source catalog stay put."
5. Else if `consumer_platform` == "Databricks":
   - primary = `DATABRICKS_TO_DATABRICKS_SHARING`, secondary = "Shared S3 External Location"
6. Else if `consumer_platform` == "Snowflake":
   - primary = `DELTA_SHARING_SNOWFLAKE`, secondary = "Iceberg REST Sharing"
   - note: Snowflake can also consume via the Iceberg REST Catalog API — consider `ICEBERG_REST_SHARING` if the consumer prefers native Iceberg tables.
7. Else if `consumer_platform` == "Power BI":
   - primary = `DELTA_SHARING_POWER_BI`, secondary = `JDBC_SQL_WAREHOUSE` (Databricks SQL Direct Connect / DirectQuery)
8. Else if `consumer_platform` in {"Python/Pandas", "Spark (non-Databricks)"}:
   - primary = `DELTA_SHARING_OPEN_PROTOCOL`, secondary = "S3 Direct Access with IAM"
9. Else (dbt, Other):
   - primary = `DELTA_SHARING_OPEN_PROTOCOL`, secondary = `JDBC_SQL_WAREHOUSE` (dbt-databricks / generic SQL connector)

Additional producer patterns — evaluate these BEFORE rules 5–10 when the corresponding need is
stated (they override platform-based selection):

- If the consumer is an **application calling over HTTP** and should not install a driver:
  - primary = `SQL_STATEMENT_EXECUTION_API`, secondary = `JDBC_SQL_WAREHOUSE`
  - note: "Programmatic access over HTTPS via the SQL Statement Execution REST API against a SQL
    warehouse — no driver install. Parameterize statements to prevent injection; use the
    EXTERNAL_LINKS disposition (pre-signed URLs) for large result sets rather than inlining JSON.
    Like JDBC, the PROVIDER pays warehouse compute per query."
- If the consumer is an **external app that must NOT hold Databricks credentials** (a managed
  gateway fronts the API):
  - primary = `API_GATEWAY_FACADE`, secondary = `SQL_STATEMENT_EXECUTION_API`
  - note: "Front the SQL Statement Execution API with a managed API gateway / OData facade. Same
    governed source as the REST API pattern, but the app only ever sees the gateway, never
    Databricks credentials. Gold + non-PII only."
- If the need is **sub-second, per-row lookups for live inference** (not analytical queries):
  - primary = `ONLINE_TABLES_MODEL_SERVING`, secondary = "(none — this is not a sharing job)"
  - note: "Publish features to Online Tables / Model Serving for sub-second per-row reads. This is
    a serving path, not a SQL-warehouse or Delta Sharing job. Anonymized gold only for
    external/ML serving."
- Last resort — if the **consumer cannot pull** at all (legacy app / relational datamart with no
  Databricks/federation/sharing path):
  - primary = `PROVIDER_PUSH_DATAMART`, secondary = "(none — no pull path exists)"
  - warning: "Copy-based, provider-owned compute, batch latency. Use ONLY when no pull path
    exists. Because the data leaves Unity Catalog, mask at source and re-tag/re-mask downstream."

#### Decision 1b: Shared-object modifier (applies to Delta Sharing solutions)

This modifier does NOT change which primary solution is selected above. It refines *what object*
you share when the primary is a Delta Sharing solution (`DELTA_SHARING_SNOWFLAKE`,
`DELTA_SHARING_POWER_BI`, `DELTA_SHARING_OPEN_PROTOCOL`, `DATABRICKS_TO_DATABRICKS_SHARING`).
Materialized View & Streaming Table sharing is GA — see "Recent Sharing Features (2025–2026)".

- If `freshness_requirement` in {"Real-time (< 1 min)", "Near real-time (< 15 min)"}:
  - shared_object = **Streaming Table** — share a Streaming Table so the consumer gets
    continuous, always-fresh data with no duplicate pipeline on their side.
  - note: "Freshness '<freshness_requirement>' → share a Streaming Table (GA) rather than a
    batch table."
- Else if the consumer needs only summaries/aggregates (not raw rows) — infer this when the
  stated need is aggregated reporting, or when `contains_pii` == "Yes" and sharing aggregates
  avoids exposing sensitive rows:
  - shared_object = **Materialized View** — share precomputed aggregates instead of raw rows
    (better security and relevance); optionally apply column mapping to rename/hide columns.
  - note: "Share a Materialized View (GA) of aggregates instead of raw tables; use column
    mapping to rename/hide columns without data rewrites."
- Else:
  - shared_object = **Table** (default; unchanged behavior).

Emit the chosen `shared_object` in the recommendation. When it is a Materialized View or
Streaming Table, the `ALTER SHARE ... ADD TABLE` statements in the generated SQL apply
unchanged (an MV/ST is added to a share the same way as a table).

#### Decision 1c: Table-format modifier (Iceberg v3 / UniForm)

This modifier does NOT change which primary solution is selected. It refines *what format the
shared table should be* so the recommendation matches the consumer's engine and workload. Apply
after Decision 1. Iceberg v3 is GA on Unity Catalog managed, foreign, and UniForm-enabled tables
(deletion vectors, row lineage/tracking, VARIANT). See "Recent Sharing Features (2025–2026)".

- If `needs_cdc` == "Yes" AND the consumer is non-Databricks (any Iceberg REST client, Snowflake,
  Trino/Flink/DuckDB, or a Spark/open-protocol consumer):
  - format_recommendation = **managed Iceberg v3**
  - note: "For cross-engine CDC, prefer managed Iceberg v3 — row lineage (permanent row ID +
    sequence number) identifies changed rows and deletion vectors apply changes without file
    rewrites, so CDC is a native property of the table readable by any Iceberg engine. This is
    stronger than Delta `WITH HISTORY` (change data feed), which the consumer's engine must
    understand."
  - (For a Databricks-to-Databricks consumer, Delta change data feed via `WITH HISTORY` remains
    fine; managed Iceberg v3 is optional.)
- If the data is semi-structured (logs, API responses, clickstream, IoT payloads) or the consumer
  needs schema-flexible columns:
  - format_recommendation = **managed Iceberg v3 with VARIANT**
  - note: "Use the Iceberg v3 VARIANT column type to share semi-structured payloads alongside
    relational columns in one governed table — no flattening, no separate store, no ETL
    normalization, and new fields are queryable without a schema migration."
- Else if `table_format` == "Delta" AND `consumer_platform` in {"Snowflake",
  "Iceberg REST client (Trino/Flink/DuckDB/etc.)"} (or the consumer otherwise reads Iceberg, e.g.
  BigQuery/Redshift/Athena/Trino):
  - format_recommendation = **UniForm (write Delta, read as Iceberg)**
  - note: "Enable UniForm so a single Delta copy is readable as Iceberg by the consumer's engine
    — no replication pipeline and no drift."
  - **Deletion-vectors caveat (important):** the enablement path decides whether deletion vectors
    (DV) may be on:
    - *UniForm / IcebergCompatV2 (the classic `delta.enableIcebergCompatV2=true` path):* DV must
      be **disabled** on the table (`delta.enableDeletionVectors=false`); you cannot enable DV on
      a Delta table with Iceberg reads enabled. If DV were previously on, run `REORG ... PURGE`
      then `OPTIMIZE`. This is the common cause of a missing `iceberg.metadata.location`.
    - *Managed Iceberg v3 (DBR 18+):* deletion vectors are part of the spec and **on by default** —
      do NOT tell the user to turn DV off here. Only the CompatV2/UniForm path needs DV off.
    So: recommend `enableDeletionVectors=false` ONLY for the UniForm/CompatV2 recommendation, not
    for a managed Iceberg v3 recommendation.
- Else: keep `table_format` as provided (no format change).

Emit `format_recommendation` in the recommendation when set, and note it does not change the
primary solution — it changes the format of the shared object.

### Decision 2: Prerequisites (add each that applies)

- `groups_exist` == "No" → "Create account-level groups in accounts.cloud.databricks.com (or via SCIM)"
- `same_metastore` == "No" AND `consumer_platform` == "Databricks" → "Exchange metastore sharing identifiers between provider and consumer"
- `consumer_identity` == "Service Principal" → "Create service principal at account level + generate OAuth credentials" AND "Add service principal to appropriate groups"
- `consumer_external` == "Yes" → "Create RECIPIENT in Unity Catalog for external consumer" AND "Generate and securely transmit activation link to consumer"
- `consumer_external` == "Yes" AND `consumer_platform` != "Databricks" → "For non-Databricks recipients who authenticate with their own IdP (Azure Entra ID, Okta, etc.), use OIDC Token Federation (GA) instead of long-lived bearer tokens in the .share profile — the recipient authenticates via their custom Identity Provider"
- `consumer_external` == "Yes" AND primary in {`DELTA_SHARING_SNOWFLAKE`, `DELTA_SHARING_POWER_BI`, `DELTA_SHARING_OPEN_PROTOCOL`, `ICEBERG_REST_SHARING`} → "If firewall/network setup is a barrier to live open-lakehouse access, consider the Delta Sharing Network Gateway (Public Preview) to let recipients access the source live with minimal manual network configuration (supports customer-managed S3/ADLS and Databricks default storage)"
- primary == `ICEBERG_REST_SHARING` → "Enable the Unity Catalog Iceberg REST Catalog API endpoint and confirm the consumer client implements Iceberg REST (Iceberg 1.11+ for scan planning / ABAC)" AND "Confirm credential vending is enabled so the consumer gets scoped storage credentials instead of broad bucket access"
- `table_format` == "Iceberg (foreign/external catalog)" → "Register the foreign Iceberg catalog in UC via a federation connector (<foreign_catalog>)" AND "Verify UC credential vending for foreign Iceberg is configured for the source storage"
- primary == `JDBC_SQL_WAREHOUSE` → "Provision a Databricks SQL warehouse (Serverless recommended) and capture its JDBC/ODBC connection details (Server Hostname, HTTP Path)" AND "Create a service principal or PAT for the consumer and GRANT it USE CATALOG/SCHEMA + SELECT on the target tables" AND "If the consumer is external or on a private network, configure PrivateLink / IP access lists for the SQL warehouse"

### Decision 3: Security measures (add each that applies)

- `contains_pii` == "Yes":
  - "Create dynamic views with column masking (is_account_group_member)"
  - "Tag PII columns with 'pii=true' classification"
  - If also `consumer_external` == "Yes":
    - measure: "DO NOT share PII tables externally. Use anonymized/aggregated gold products only."
    - warning: "PII + External consumer = HIGH RISK. Share only aggregated/anonymized data."
- `needs_column_security` == "Yes" → "Create secure views with CASE WHEN is_account_group_member() logic"
- `needs_row_security` == "Yes":
  - "Create filtered views with row-level predicates based on group membership"
  - "Or: Use partition-based sharing (share only relevant partitions)"
- `data_classification` in {"Confidential", "Restricted"}:
  - "Enable audit logging (system.access.audit)"
  - "Require VPC PrivateLink for data access (no public internet)"
  - "Review with security team before enabling sharing"
- primary == `ICEBERG_REST_SHARING` AND (`needs_column_security` == "Yes" OR `needs_row_security` == "Yes" OR `contains_pii` == "Yes"):
  - "Use cross-engine Attribute-Based Access Control (ABAC, Beta) for direct query access (not sharing): define column masks, row filters, and tag-based policies once in UC; UC evaluates them during server-side Iceberg REST scan planning and returns a filtered scan plan so an engine querying UC directly only reads authorized data"
  - "Prefer ABAC over per-engine view logic when multiple external Iceberg engines query the same UC table directly — governance is enforced in UC, not duplicated per engine"
  - "IMPORTANT — ABAC on a Delta *share* does NOT restrict the recipient. A provider can add ABAC-secured tables/schemas to a share, but the recipient receives full access to the shared asset and applies their OWN ABAC on their side. To limit what an external RECIPIENT sees, share a Materialized View of aggregates, a filtered/secure view, or only the relevant partitions — do not rely on provider ABAC to mask a recipient's copy."
- primary == `JDBC_SQL_WAREHOUSE`:
  - "Governance is enforced live at query time — apply UC grants and dynamic views (column masking / row filters) on the SQL warehouse; the consumer only sees what their principal is authorized to read"
  - "Prefer OAuth service principal credentials over long-lived PATs; rotate/scope tokens and restrict to the specific catalog/schema"
- `data_residency` != "No restriction":
  - warning: "Data residency: '<value>' — verify sharing doesn't violate this."
  - If also `same_region` == "No" → warning: "Cross-region sharing may violate data residency. Consider local replica or filtered share."
  - If primary == `JDBC_SQL_WAREHOUSE` → note: "JDBC keeps data in the provider region (no copy) — a good fit for residency constraints since the consumer queries in place."

### Decision 4: Cost considerations (add each that applies, then always add the last two)

- `same_region` == "No":
  - "S3 cross-region egress: ~$0.02/GB (<provider_region> → <consumer_region>)"
  - If `data_volume` in {"Large (100 GB - 1 TB)", "Very Large (> 1 TB)"} → "HIGH VOLUME + CROSS-REGION: Consider S3 replication to consumer region to reduce egress"
- `data_volume` == "Very Large (> 1 TB)" → "Large dataset: ensure tables are partitioned for efficient predicate pushdown"
- `freshness_requirement` in {"Real-time (< 1 min)", "Near real-time (< 15 min)"} → "Real-time freshness requires streaming pipeline (higher compute cost)"
- primary == `ICEBERG_REST_SHARING` → "Managed Iceberg tables get Predictive Optimization + Liquid Clustering automatically — no manual OPTIMIZE/VACUUM tuning, and layout improvements (data skipping) also benefit external engines like Spark/Trino/DuckDB"
- primary == `JDBC_SQL_WAREHOUSE`:
  - "Unlike Delta Sharing, the PROVIDER pays SQL warehouse compute for every consumer query — right-size the warehouse and use auto-stop; Serverless minimizes idle cost"
  - "Consider a dedicated warehouse per consumer/workload for cost attribution and isolation"
  - "This overrides the generic 'zero provider compute' note below — that applies to Delta Sharing / Iceberg REST, not JDBC"
- If primary != `JDBC_SQL_WAREHOUSE`:
  - Always: "Provider: Zero compute cost for Delta Sharing / Iceberg REST reads (no cluster involved)"
  - Always: "Consumer: Pays their own compute for query execution"

## Solution Catalog

| Solution ID | Name | Description | Complexity | Latency | Cost |
|-------------|------|-------------|-----------|---------|------|
| `DIRECT_GRANT_WITH_VIEWS` | Direct GRANT + Cross-Catalog Views | Same metastore — grant SELECT directly and consumer creates views in their catalog. | Low | Zero (live read from same Delta tables) | Zero additional (same S3, same region) |
| `DATABRICKS_TO_DATABRICKS_SHARING` | Databricks-to-Databricks (D2D) Sharing | Different metastores but both Databricks — uses Delta Sharing with native catalog integration. | Medium | Near zero (metadata auto-sync, live reads via pre-signed URLs) | S3 egress if cross-region, zero compute for sharing |
| `DELTA_SHARING_SNOWFLAKE` | Delta Sharing → Snowflake | Open protocol sharing to Snowflake — tables appear as native Snowflake external tables. | Medium | Minutes (Snowflake refreshes on query) | S3 egress + Snowflake compute on consumer side |
| `DELTA_SHARING_POWER_BI` | Delta Sharing → Power BI | Share data to Power BI via Delta Sharing connector — Import or DirectQuery mode. | Low-Medium | Scheduled refresh (Import) or real-time (DirectQuery) | S3 egress + Power BI Pro/Premium license |
| `DELTA_SHARING_OPEN_PROTOCOL` | Delta Sharing (Open Protocol) | Generic open protocol — works with Python, Spark, any Delta Sharing client. | Low-Medium | On-demand (reads when consumer queries) | S3 egress + consumer's compute |
| `SHARED_EXTERNAL_LOCATION` | Shared S3 External Location | Both parties access same S3 path via separate IAM roles. Supports read-write. | High | Depends on write frequency | S3 storage + IAM management overhead |
| `ICEBERG_REST_SHARING` | Unity Catalog Iceberg REST Sharing | Share live data to any Iceberg REST-compatible client (Trino, Flink, DuckDB, Spark, Snowflake) via UC's Iceberg REST Catalog API over the open Delta Sharing protocol. Works for managed and foreign Iceberg tables; governance (incl. cross-engine ABAC) and credential vending stay in UC. | Medium | On-demand (live reads, no copies) | S3 egress + consumer compute; zero provider compute; auto-optimized tables |
| `JDBC_SQL_WAREHOUSE` | JDBC/ODBC over Databricks SQL Warehouse | Consumer connects live to a Databricks SQL warehouse via JDBC/ODBC (BI tools, apps, dbt). Data stays in Databricks; UC grants + dynamic views + ABAC enforce governance at query time. No dataset copy. | Low-Medium | Live (interactive query latency) | Provider pays SQL warehouse compute for each query; no egress if consumer is remote client |
| `SQL_STATEMENT_EXECUTION_API` | SQL Statement Execution REST API | App calls over HTTPS against a SQL warehouse — no driver install. Parameterized statements; EXTERNAL_LINKS disposition for large exports. UC-governed. | Low-Medium | Live | Provider pays SQL warehouse compute per query |
| `API_GATEWAY_FACADE` | API Gateway / OData Facade | A managed gateway fronts the SQL Statement Execution API so the external app never holds Databricks credentials. Same governed source; gold + non-PII only. | Medium | Live | Provider pays warehouse compute + gateway |
| `PROVIDER_PUSH_DATAMART` | Provider PUSH to Consumer Datamart | Copy-based, last resort when the consumer cannot pull. Provider pushes governed gold on a schedule; data leaves UC so re-mask/re-tag downstream. | Medium-High | Batch | Provider owns compute; copy storage on consumer |
| `ONLINE_TABLES_MODEL_SERVING` | Online Tables / Model Serving | Sub-second per-row lookups for live inference. Not a SQL-warehouse or sharing job. Anonymized gold only for external/ML serving. | Medium | Sub-second (serving) | Provider pays serving compute |
| `CONSUME_D2D_SHARE` | Consume: Mount D2D Share as Catalog | (Consumer) Mount a provider's Delta share as a catalog and query live; provider masks/row filters enforced. | Low | Live (zero-copy) | Consumer compute; S3 egress if cross-region |
| `LAKEHOUSE_FEDERATION` | Consume: Lakehouse Federation | (Consumer) Register a query engine (Snowflake/Postgres/Redshift/BigQuery) as a foreign catalog and push queries down — no ingestion pipeline. | Medium | Live (query in place) | Source engine compute |
| `CATALOG_FEDERATION` | Consume: Catalog Federation (Glue/Hive) | (Consumer) Federate a whole Glue/Hive metastore into UC as a foreign catalog; read all registered tables via one namespace, governed identically. | Medium | Live | Consumer compute |
| `EXTERNAL_LOCATION_READ` | Consume: Partner S3 External Location | (Consumer) Register a partner's S3 path with a read-only cross-account IAM role and read Delta/Parquet in place — no duplicate storage. | Low-Medium | Live | Consumer compute; cross-account egress |
| `CONSUME_OPEN_DELTA_SHARING` | Consume: Open Delta Sharing Feed | (Consumer) Read a vendor's open Delta Sharing feed via Spark/`delta-sharing` from a `.share` profile; works even if the vendor is not on Databricks. | Low | On read | Consumer compute; S3 egress |

**Recent capabilities that apply across the Delta Sharing solutions above** (see "Recent
Sharing Features (2025–2026)" for sources):
- **Materialized View & Streaming Table sharing (GA):** any `DELTA_SHARING_*` /
  `DATABRICKS_TO_DATABRICKS_SHARING` solution can share a live Materialized View (precomputed
  aggregates — share only insights, not raw rows) or a Streaming Table (continuous, always-fresh
  data). Recipients can build views and their own MV/ST pipelines on top of shared MV/STs.
  Prefer an ST over a raw table when the consumer needs real-time freshness.
- **Share to any Iceberg client (GA):** Delta Sharing to external Iceberg clients (e.g.
  Snowflake, Trino) with full transactional consistency and vended storage credentials — this
  strengthens `ICEBERG_REST_SHARING` and the Snowflake/open-protocol paths.

## Implementation Steps by Solution

Substitute `<consumer_slug>`, `<consumer_name>`, `<tables>` from inputs. `tables_to_share` is a
Unity Catalog three-level name (`catalog.schema.table` or `catalog.schema.*`): `<catalog>` = the
part before the first `.`, `<schema>` = the middle part between the first and second `.` (fallback
catalog `demo_sales`, schema `gold_products`).

### DIRECT_GRANT_WITH_VIEWS
1. Create account-level group for `<consumer_name>`
2. `GRANT USE CATALOG ON CATALOG demo_sales TO \`<consumer_slug>\``
3. `GRANT USE SCHEMA ON SCHEMA demo_sales.<schema> TO \`<consumer_slug>\``
4. `GRANT SELECT ON TABLE/SCHEMA demo_sales.<tables> TO \`<consumer_slug>\``
5. Consumer creates views in their catalog referencing demo_sales tables
6. Document in table comments + add tags
7. Set up audit monitoring

### DATABRICKS_TO_DATABRICKS_SHARING
1. Get consumer metastore sharing identifier (consumer runs: `SELECT current_metastore()`)
2. Provider: `CREATE SHARE sales_share`
3. Provider: `ALTER SHARE sales_share ADD TABLE demo_sales.<tables>`
4. Provider: `CREATE RECIPIENT <consumer_slug> USING ID '<consumer-sharing-id>'`
5. Provider: `GRANT SELECT ON SHARE sales_share TO RECIPIENT <consumer_slug>`
6. Consumer: `CREATE PROVIDER sales_provider USING ID '<provider-sharing-id>'`
7. Consumer: `CREATE CATALOG sales_shared USING SHARE sales_provider.sales_share`
8. Consumer: `GRANT USE CATALOG ON sales_shared TO their local groups`
9. Consumer: query via `SELECT * FROM sales_shared.gold_products.*`

### DELTA_SHARING_SNOWFLAKE
1. Provider: `CREATE SHARE sales_share`
2. Provider: `ALTER SHARE sales_share ADD TABLE demo_sales.<tables>`
3. Provider: `CREATE RECIPIENT snowflake_consumer`
4. Provider: `GRANT SELECT ON SHARE ... TO RECIPIENT snowflake_consumer`
5. Send activation link to Snowflake admin
6. Snowflake: `CREATE CATALOG INTEGRATION ... DELTA_SHARING`
7. Snowflake: `CREATE DATABASE FROM DELTA_SHARING_SHARE`
8. Snowflake: query as native tables

### DELTA_SHARING_POWER_BI
1. Provider: `CREATE SHARE sales_share`
2. Provider: `ALTER SHARE sales_share ADD TABLE demo_sales.<tables>`
3. Provider: `CREATE RECIPIENT powerbi_consumer`
4. Provider: `GRANT SELECT ON SHARE ... TO RECIPIENT powerbi_consumer`
5. Download .share profile from activation link
6. Power BI: Get Data → Delta Sharing connector
7. Power BI: Paste sharing profile URL
8. Power BI: Select tables and build visuals
9. Set up scheduled refresh (Import mode) or DirectQuery

### DELTA_SHARING_OPEN_PROTOCOL
1. Provider: `CREATE SHARE sales_share`
2. Provider: `ALTER SHARE sales_share ADD TABLE demo_sales.<tables>`
3. Provider: `CREATE RECIPIENT <consumer_slug>`
4. Provider: `GRANT SELECT ON SHARE ... TO RECIPIENT <consumer_slug>`
5. Send activation link to consumer (they download .share profile)
6. Consumer: `pip install delta-sharing`
7. Consumer: `delta_sharing.load_as_pandas('<profile>#share.schema.table')`
8. Consumer: process data in their environment

### SHARED_EXTERNAL_LOCATION
1. Create shared S3 bucket (or path) accessible by both parties
2. Create IAM role for provider (read+write)
3. Create IAM role for consumer (read-only or read-write)
4. Provider: `CREATE EXTERNAL LOCATION` pointing to S3 path
5. Consumer: `CREATE EXTERNAL LOCATION` with their IAM role
6. Consumer: `CREATE TABLE ... LOCATION 's3://shared-bucket/path/'`
7. Both: set up access via Unity Catalog storage credentials
8. Manage via Terraform for consistency

### ICEBERG_REST_SHARING
1. Ensure the shared tables are managed Iceberg in UC, or a foreign Iceberg table registered in UC via a federation connector (`<foreign_catalog>`)
2. Provider: `CREATE SHARE <consumer_slug>_share`
3. Provider: `ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.<tables>` (Iceberg is a first-class source and destination format)
4. Provider: `CREATE RECIPIENT <consumer_slug>` (add `USING ID` for Databricks-to-Databricks; omit for open/Iceberg clients)
5. Provider: `GRANT SELECT ON SHARE <consumer_slug>_share TO RECIPIENT <consumer_slug>`
6. Provider (governance): define ABAC policies in UC (column masks / row filters / tag-based) so they are enforced during Iceberg REST scan planning for every external engine
7. Send the Iceberg REST Catalog endpoint + credentials (activation link / OAuth) to the consumer
8. Consumer: point their Iceberg REST client (Trino/Flink/DuckDB/Spark/Snowflake) at UC's Iceberg REST Catalog API and query the shared tables live — no ingestion or copies
9. Provider retains access control, auditing, and governance in UC; managed tables stay auto-optimized via Predictive Optimization

### JDBC_SQL_WAREHOUSE
1. Provision a Databricks SQL warehouse (Serverless recommended); note Server Hostname + HTTP Path
2. Provider: grant the consumer principal `USE CATALOG` / `USE SCHEMA` / `SELECT` on the target tables
3. Provider (optional governance): create dynamic views with column masking / row filters and grant on those instead of base tables
4. Create a service principal (OAuth, preferred) or PAT for the consumer; scope to the catalog/schema
5. If external/private: configure PrivateLink or IP access lists on the SQL warehouse
6. Send the consumer: JDBC URL (host + HTTP path), auth (OAuth client id/secret or token), and the catalog/schema
7. Consumer: install the Databricks JDBC/ODBC driver (or `databricks-sql-connector` for Python, `dbt-databricks` for dbt) and connect
8. Consumer: query the shared tables/views live; provider's warehouse executes and governance is enforced per query

## Generated SQL / Code Templates

Emit the block matching the primary solution. Replace `<consumer_slug>`, `<consumer_name>`,
`<consumer_platform>`, and table names from inputs.

### DIRECT_GRANT_WITH_VIEWS
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

### DATABRICKS_TO_DATABRICKS_SHARING
```sql
-- PROVIDER SIDE
CREATE SHARE IF NOT EXISTS <consumer_slug>_share
COMMENT 'Data products shared with <consumer_name>';

ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.revenue_dashboard;
ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.customer_segments;
ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.product_catalog_public;

-- Materialized View / Streaming Table sharing is GA — add an MV/ST just like a table.
-- Per Decision 1b: Streaming Table for real-time freshness, Materialized View for aggregates.
ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.daily_revenue_mv;   -- Materialized View
ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.live_orders_st;      -- Streaming Table

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

### DELTA_SHARING_SNOWFLAKE / DELTA_SHARING_POWER_BI / DELTA_SHARING_OPEN_PROTOCOL
Provider side is common; the consumer side differs by platform.

```sql
-- PROVIDER SIDE (run in Databricks)
CREATE SHARE IF NOT EXISTS <consumer_slug>_share
COMMENT 'Data products for <consumer_name> (<consumer_platform>)';

ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.revenue_dashboard;
ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.customer_segments;
ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.product_catalog_public;

-- If needs_cdc == "Yes", also enable change data feed:
ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.revenue_dashboard
  WITH HISTORY;

-- Sharing a Materialized View or Streaming Table (GA): add it exactly like a table.
-- Use when Decision 1b picks shared_object = Materialized View (aggregates) or Streaming Table
-- (real-time freshness). Replace with your MV/ST name.
ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.daily_revenue_mv;   -- Materialized View
ALTER SHARE <consumer_slug>_share ADD TABLE demo_sales.gold_products.live_orders_st;      -- Streaming Table
-- (Optional) share a view built on top of an MV/ST, or use column mapping to rename/hide columns.

CREATE RECIPIENT IF NOT EXISTS <consumer_slug>
  COMMENT '<consumer_name> - <consumer_platform>';

GRANT SELECT ON SHARE <consumer_slug>_share TO RECIPIENT <consumer_slug>;
-- Get activation link: Data Explorer → Delta Sharing → Recipients → <consumer_slug> → Activation Link
SHOW GRANTS TO RECIPIENT <consumer_slug>;
```

Consumer side — Snowflake:
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

Consumer side — Power BI:
```
1. Get Data → More... → Delta Sharing
2. Enter the sharing profile URL from activation link
3. Select tables: revenue_dashboard, customer_segments
4. Choose: Import (scheduled refresh) or DirectQuery (live)
5. Build visuals, publish to Power BI Service
6. Set scheduled refresh (recommended: daily)
```

Consumer side — Python/Pandas or Spark (non-Databricks):
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

### SHARED_EXTERNAL_LOCATION
```sql
-- Provider workspace
CREATE STORAGE CREDENTIAL IF NOT EXISTS provider_shared_cred
  WITH (AWS_IAM_ROLE = 'arn:aws:iam::PROVIDER_ACCOUNT:role/shared-write-role');

CREATE EXTERNAL LOCATION IF NOT EXISTS shared_exchange
  URL 's3://shared-data-exchange/sales-to-finance/'
  WITH (STORAGE CREDENTIAL provider_shared_cred);

-- Consumer workspace
CREATE STORAGE CREDENTIAL IF NOT EXISTS consumer_shared_cred
  WITH (AWS_IAM_ROLE = 'arn:aws:iam::CONSUMER_ACCOUNT:role/shared-read-role');

CREATE EXTERNAL LOCATION IF NOT EXISTS shared_exchange
  URL 's3://shared-data-exchange/sales-to-finance/'
  WITH (STORAGE CREDENTIAL consumer_shared_cred);

CREATE TABLE IF NOT EXISTS <consumer_slug>_catalog.shared.revenue
  USING DELTA
  LOCATION 's3://shared-data-exchange/sales-to-finance/revenue_dashboard';
```

### ICEBERG_REST_SHARING
```sql
-- PROVIDER SIDE (Databricks / Unity Catalog)

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

Consumer side — any Iceberg REST client (example: PyIceberg / Spark / Trino / DuckDB):
```python
# Consumer points an Iceberg REST client at UC's Iceberg REST Catalog API.
# Example with PyIceberg:
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

### JDBC_SQL_WAREHOUSE
```sql
-- PROVIDER SIDE (Databricks / Unity Catalog)
-- Grant the consumer principal read access on the target schema/tables
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

```python
# CONSUMER SIDE — Python (databricks-sql-connector)
# pip install databricks-sql-connector
from databricks import sql

with sql.connect(
    server_hostname="<workspace>.cloud.databricks.com",   # from SQL warehouse
    http_path="/sql/1.0/warehouses/<warehouse-id>",        # from SQL warehouse
    access_token="<OAUTH_OR_PAT_TOKEN>",                   # scoped consumer credential
) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM demo_sales.gold_products.revenue_shared LIMIT 10")
        for row in cur.fetchall():
            print(row)
```

```text
# CONSUMER SIDE — generic JDBC URL (BI tools / apps)
jdbc:databricks://<workspace>.cloud.databricks.com:443/default;
  transportMode=http;ssl=1;
  httpPath=/sql/1.0/warehouses/<warehouse-id>;
  AuthMech=11;Auth_Flow=0;   # OAuth (or AuthMech=3 + PAT)

# CONSUMER SIDE — dbt (profiles.yml, dbt-databricks)
# type: databricks
# host: <workspace>.cloud.databricks.com
# http_path: /sql/1.0/warehouses/<warehouse-id>
# token: <OAUTH_OR_PAT_TOKEN>
# catalog: demo_sales
# schema: gold_products
```

## Architecture Diagrams

Emit the diagram matching the primary solution.

### DIRECT_GRANT_WITH_VIEWS
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

### DATABRICKS_TO_DATABRICKS_SHARING
```
┌───────────────────────────┐           ┌───────────────────────────┐
│  PROVIDER WORKSPACE       │  Delta    │  CONSUMER WORKSPACE       │
│  Metastore A              │  Sharing  │  Metastore B              │
│  demo_sales.gold_products │──────────►│  sales_shared (CATALOG)   │
│  S3: s3://provider-bucket │◄──────────│  Reads via pre-signed URLs│
└───────────────────────────┘  direct   └───────────────────────────┘
  Auth: Metastore-to-metastore (automatic)  Cost: S3 egress if cross-region
```

### DELTA_SHARING_SNOWFLAKE / POWER_BI / OPEN_PROTOCOL
```
┌───────────────────────────┐           ┌───────────────────────────┐
│  DATABRICKS (Provider)    │  Delta    │  <consumer_platform>      │
│  demo_sales.gold_products │  Sharing  │  Reads via .share profile │
│  SHARE / RECIPIENT        │──────────►│  Tables appear native     │
│  S3: s3://provider-bucket │◄──────────│  pre-signed S3 URLs       │
└───────────────────────────┘  HTTPS    └───────────────────────────┘
  Auth: Bearer token in .share profile   Cost: S3 egress + consumer compute
```

### SHARED_EXTERNAL_LOCATION
```
┌───────────────────────────┐           ┌───────────────────────────┐
│  PROVIDER (IAM: write)    │           │  CONSUMER (IAM: read/write)│
└─────────────┬─────────────┘           └─────────────┬─────────────┘
              ▼                                       ▼
         ┌─────────────────────────────────────────────────┐
         │   S3: s3://shared-bucket/path/ (Delta tables)    │
         │   Both parties access same files                 │
         └─────────────────────────────────────────────────┘
  Auth: Separate IAM roles trusting each Unity Catalog
```

### ICEBERG_REST_SHARING
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

### JDBC_SQL_WAREHOUSE
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

### Additional producer patterns

`SQL_STATEMENT_EXECUTION_API` / `API_GATEWAY_FACADE`
```
┌───────────────────────────────┐        ┌──────────────────────────────┐
│  DATABRICKS (Provider)        │ HTTPS  │  App / gateway               │
│  SQL Warehouse + UC grants    │◄───────│  POST /sql/statements        │
│  demo_sales.gold_products     │───────►│  rows (INLINE / EXTERNAL_LINKS)│
│  (API_GATEWAY_FACADE: a       │  REST  │  gateway hides DBX creds     │
│   managed gateway fronts this)│        │                              │
└───────────────────────────────┘        └──────────────────────────────┘
  No driver install. Provider pays warehouse compute per query.
```

`ONLINE_TABLES_MODEL_SERVING`
```
┌───────────────────────────────┐        ┌──────────────────────────────┐
│  DATABRICKS (Provider)        │  HTTPS │  Inference client / app      │
│  Online Table / Serving       │◄──────►│  sub-second per-row lookups  │
│  (features from gold)         │  serve │                              │
└───────────────────────────────┘        └──────────────────────────────┘
  Serving path, NOT a warehouse/sharing job. Anonymized gold only for external.
```

`PROVIDER_PUSH_DATAMART` (last resort)
```
┌───────────────────────────────┐  push  ┌──────────────────────────────┐
│  DATABRICKS (Provider)        │  JDBC  │  Consumer datamart (legacy)  │
│  scheduled job: filter gold   │───────►│  stg table → MERGE into target│
│  mask at source (leaves UC)   │  batch │  copy lives here             │
└───────────────────────────────┘        └──────────────────────────────┘
  Copy-based, provider owns compute, batch latency. Re-tag/re-mask downstream.
```

## Consumer Architecture Diagrams

Emit the diagram matching the consumer solution (Decision 1-C). In all of these YOU are the
consumer bringing data in; the default is query-in-place, not copy-in.

### CONSUME_D2D_SHARE
```
┌───────────────────────────┐  Delta   ┌───────────────────────────┐
│  PROVIDER (another DBX)   │  Sharing │  YOU (Consumer, Databricks)│
│  finance_share            │─────────►│  CREATE CATALOG USING SHARE│
│  S3: s3://provider-bucket │◄─────────│  query live, masks enforced│
└───────────────────────────┘  live    └───────────────────────────┘
  Zero-copy; data stays in provider S3. Cross-region = S3 egress.
```

### LAKEHOUSE_FEDERATION
```
┌───────────────────────────┐  JDBC    ┌───────────────────────────┐
│  SOURCE ENGINE            │  push-   │  YOU (Consumer, Databricks)│
│  Snowflake/Postgres/etc.  │  down    │  FOREIGN CATALOG over      │
│  (data stays put)         │◄────────►│  CONNECTION; join live     │
└───────────────────────────┘  query   └───────────────────────────┘
  No ingestion pipeline; source engine runs the pushed-down query.
```

### CATALOG_FEDERATION (Glue / Hive)
```
┌───────────────────────────┐          ┌───────────────────────────┐
│  AWS Glue / Hive Metastore│  feder-  │  YOU (Consumer, UC)        │
│  many registered S3 tables│  ate     │  FOREIGN CATALOG glue_*    │
│  s3://glue-backed/...      │◄────────►│  one catalog.schema.table  │
└───────────────────────────┘          │  namespace, governed by UC │
                                        └───────────────────────────┘
  UC routes Glue-backed S3 and UC-managed tables identically.
```

### EXTERNAL_LOCATION_READ (partner S3)
```
┌───────────────────────────┐          ┌───────────────────────────┐
│  PARTNER S3 BUCKET        │  read-   │  YOU (Consumer, Databricks)│
│  s3://partner-feed/...     │  only    │  STORAGE CREDENTIAL +      │
│  Delta/Parquet files       │◄─────────│  EXTERNAL LOCATION; read   │
└───────────────────────────┘  IAM role│  in place (no copy)        │
                                        └───────────────────────────┘
  Cross-account read-only IAM role. COPY INTO only for a local snapshot.
```

### CONSUME_OPEN_DELTA_SHARING
```
┌───────────────────────────┐  Delta   ┌───────────────────────────┐
│  VENDOR (any platform)    │  Sharing │  YOU (Consumer)            │
│  open .share profile       │  (open)  │  spark.read.format(        │
│  pre-signed S3 URLs        │─────────►│  'deltaSharing'); persist  │
└───────────────────────────┘  HTTPS   │  to bronze only if needed  │
                                        └───────────────────────────┘
  Works even if the vendor is not on Databricks.
```

## Output Format

Present the recommendation in this order:
0. Collaboration modality (Decision 0): state whether this is direct table sharing, Clean Rooms, Marketplace, or AI-asset sharing, and why. For a non-table-sharing modality, lead with its note as the primary recommendation and treat the rest of this list as applying to any supporting tabular data.
1. Recommended architecture: primary solution name, description, complexity, latency, cost, and the alternative. When the primary is a Delta Sharing solution, also state the `shared_object` from Decision 1b (Table, Materialized View, or Streaming Table) and why. State the `format_recommendation` from Decision 1c (managed Iceberg v3 / VARIANT / UniForm) when set.
2. Prerequisites (or "No special prerequisites. Ready to implement." if none).
3. Security measures (or "Standard security (Unity Catalog default governance applies)." if none) and any warnings.
4. Cost considerations.
5. Implementation steps.
6. Generated SQL/code for the primary solution.
7. Architecture diagram for the primary solution.
8. Input summary recap.

## Unity Catalog + Apache Iceberg Reference

Context for the Iceberg-related decisions above. Source: Databricks blog,
"Advancing Apache Iceberg on Databricks: Iceberg v3 GA, Open Sharing, and Unified Governance"
(https://www.databricks.com/blog/unity-catalog-and-next-era-apache-icebergtm). Content was
rephrased for compliance with licensing restrictions.

The catalog — not just the table format — determines whether open data can be governed,
optimized, and shared consistently across engines. UC positions itself as an interoperable
Iceberg catalog across five capability areas:

1. Open APIs + credential vending — Managed Iceberg is GA: create/read/write Iceberg tables in
   UC from any engine (Spark, Trino, Flink, Snowflake, DuckDB, pandas) via UC's Iceberg REST
   Catalog API, without copying data or granting broad storage permissions. UC also vends
   credentials for federated (foreign) Iceberg tables. Iceberg-compatible materialized views
   are in gated preview (`CREATE MATERIALIZED VIEW ... USING ICEBERG`).
2. Catalog federation — Foreign Iceberg is GA: UC can govern Iceberg tables managed in other
   catalogs (AWS Glue, Snowflake Horizon, Hive Metastore, Google Cloud Lakehouse, Palantir,
   Salesforce, Workday) while data and source catalog stay in place — a single pane of glass.
3. Cross-engine ABAC (Beta) — Define column masks, row filters, and tag-based policies once in
   UC. When an external Iceberg engine queries UC directly, UC evaluates policies during
   server-side scan planning and returns a filtered scan plan, so engines only read authorized
   data. Any client implementing Iceberg REST scan planning (Iceberg 1.11+) enforces this. Note
   this governs *direct query access*, not what a Delta Sharing recipient sees — see area 4.
4. Zero-copy secure sharing — Iceberg is a first-class source and destination in Delta Sharing.
   Sharing to Iceberg REST clients is GA; recipients (Snowflake, Trino, Flink, Spark) query
   shared data live with no manual ingestion. Foreign Iceberg sharing is in Public Preview.
   ABAC and sharing interact carefully: a provider can add ABAC-secured tables/schemas to a
   share, but the ABAC policy does NOT govern the recipient — the recipient gets full access to
   the shared asset and can apply their own ABAC. To restrict what an external recipient sees,
   share an aggregated Materialized View, a secure/filtered view, or only specific partitions.
5. Performance/format innovation — Predictive Optimization + Liquid Clustering keep tables fast
   without manual tuning, and layout improvements benefit external engines too. Iceberg v3 is
   GA (deletion vectors, row tracking, VARIANT) across managed, foreign, and UniForm tables;
   these work across both Delta and Iceberg without rewriting data. Iceberg v4 (adaptive
   metadata tree) is the next step, with Delta 5.0 proposed to adopt the same structure.

When to lean on Iceberg in this advisor:
- Consumer runs a non-Databricks Iceberg engine → `ICEBERG_REST_SHARING`.
- Data lives in an external catalog you don't want to migrate → register as Foreign Iceberg and
  share in place.
- Multiple external engines hit the same table with row/column security needs → use ABAC rather
  than per-engine views.

## Escalation Ladder (prefer the top rung that fits)

When more than one pattern could work, prefer the highest zero-copy, Unity Catalog-governed rung
before dropping to a copy-based one. Rank from most to least preferred:

1. **Direct GRANT + views** (same metastore) — zero copy, zero extra cost.
2. **D2D Delta Sharing** (different metastore, both Databricks) — native, token-free.
3. **Lakehouse / Catalog Federation** (consumer side) · **UniForm + Iceberg REST** (producer,
   non-Databricks Iceberg consumer) — live, zero-copy, governed.
4. **JDBC/ODBC** or **SQL Statement Execution API** (+ **API Gateway facade** when the app can't
   hold credentials) — live query; provider pays compute.
5. **Open Delta Sharing** — broadest reach; on-read.
6. **Provider PUSH / copy** — last resort, only when the consumer cannot pull.

Notes: **Online Tables / Model Serving** is off-ladder — it is a serving path for sub-second
per-row lookups, not an analytical sharing rung. **DEEP CLONE** is a writable-snapshot pattern,
not an access rung: it drops governance, so re-tag and re-mask after cloning.

## Best Practices

- Pick the collaboration modality first (Decision 0). Direct table sharing is not always the answer: use **Clean Rooms** when raw data must not be exposed (especially PII + external), the **Marketplace** for broad/unknown audiences, and **AI-asset sharing / Genie Agent Sharing** for models, agents, or conversational access.
- Confirm the metastore/account/region topology first — Decision 1 short-circuits on `access_type` (read-write) and `same_metastore` before platform is even considered.
- Match the shared table format to the consumer (Decision 1c): managed **Iceberg v3** for cross-engine CDC (row lineage + deletion vectors), **VARIANT** for semi-structured data, and **UniForm** to let an Iceberg-reading consumer (Snowflake/Trino/BigQuery/etc.) read a single Delta copy with no replication.
- Delta Sharing is read-only. Any read-write requirement routes to `SHARED_EXTERNAL_LOCATION` regardless of platform.
- Never share PII externally; for `contains_pii` + `consumer_external`, share only aggregated/anonymized gold products.
- For Confidential/Restricted data, enable audit logging and require PrivateLink, and get a security review before enabling sharing.
- Watch cross-region egress cost for Large/Very Large volumes; consider S3 replication to the consumer region.
- Treat the generated SQL as a starting template — replace catalog/schema/table names, sharing IDs, and IAM ARNs with real values before running.
- For any non-Databricks Iceberg consumer, prefer `ICEBERG_REST_SHARING` (live, zero-copy, governed) over exporting files; managed Iceberg stays auto-optimized and read-write from any engine.
- Enforce row/column governance for external Iceberg engines that query UC directly with cross-engine ABAC in UC rather than duplicating view logic per engine. But note ABAC does NOT restrict a Delta Sharing recipient — to limit what a recipient sees, share an aggregated Materialized View, a secure/filtered view, or specific partitions.
- To bring an external Iceberg estate under governance without moving data, register it as Foreign Iceberg via a federation connector and share it in place.
- Choose `JDBC_SQL_WAREHOUSE` for live, governed SQL access from BI tools/apps/dbt when a copy or share protocol isn't wanted — but remember the provider (not the consumer) pays SQL warehouse compute per query, so right-size and auto-stop the warehouse.
- For JDBC, prefer OAuth service principals over long-lived PATs and enforce governance with UC grants + dynamic views so each consumer principal only reads authorized rows/columns.
- When `freshness_requirement` is real-time or near real-time, prefer sharing a **Streaming Table** (GA) so the consumer gets always-fresh data with no duplicate pipeline; when the consumer only needs aggregates or summaries, share a **Materialized View** (GA) instead of raw tables. See "Recent Sharing Features (2025–2026)".
- For cross-cloud or egress-sensitive sharing, mention **SecureConnect** (cross-cloud connectivity) and **Global Distribution** (automatic replication to cut egress); for regulated cross-boundary sharing, mention **cross-regulatory-domain sharing**.

## Recent Sharing Features (2025–2026)

Newer Databricks sharing capabilities the advisor should factor in. Content was rephrased for
compliance with licensing restrictions.

### OpenSharing — the next evolution of Delta Sharing
Source: Databricks, "Announcing New OpenSharing and Marketplace capabilities for the AI era"
(https://www.databricks.com/blog/announcing-new-opensharing-and-marketplace-capabilities-ai-era)
and "Introducing OpenSharing"
(https://www.databricks.com/blog/introducing-opensharing-next-evolution-delta-sharing-agentic-era).

Delta Sharing is becoming OpenSharing, now a Linux Foundation project: an open, vendor-neutral
protocol that extends zero-copy sharing from tables to AI assets. New capabilities group into
four pillars:
1. **Open client interoperability** — Share to any Iceberg client (GA, incl. Snowflake and
   Trino) with transactional consistency; high-performance open-client sharing via vended
   storage credentials (GA); share Lakebase tables and their change data feed (Public Preview);
   share foreign Iceberg tables from Glue, Snowflake Open Catalog, or any Iceberg REST catalog
   (GA coming soon).
2. **Agentic sharing** — Genie Agent Sharing (Beta): share conversational, natural-language
   access to your data with external partners.
3. **Secure, governed multi-cloud sharing** — SecureConnect (Public Preview) for one-click
   cross-cloud storage connectivity (AWS/Azure/GCP); Global Distribution (Private Preview) for
   automatic cross-region/cross-cloud replication to cut egress; cross-regulatory-domain sharing
   (Public Preview) across boundaries like GovCloud and commercial clouds.
4. **Friction-free sharing** — Email-based sharing (coming soon); Change Data Feed on shared
   views (Private Preview).

**How this affects recommendations:**
- Consumer on a non-Databricks Iceberg engine (Snowflake, Trino) → share-to-any-Iceberg-client
  is GA; reinforces choosing `ICEBERG_REST_SHARING`.
- Cross-cloud or cross-region sharing with egress concerns → mention SecureConnect and Global
  Distribution as ways to connect across clouds and reduce egress.
- Regulated cross-boundary sharing (e.g. GovCloud ↔ commercial) → note cross-regulatory-domain
  sharing (Public Preview) instead of building a manual replica.
- Consumer wants conversational/AI access rather than raw tables → note Genie Agent Sharing (Beta).

### Materialized View & Streaming Table (MV/ST) Sharing — GA
Source: Databricks, "Now GA: Share Materialized Views and Streaming Tables with Delta Sharing"
(https://www.databricks.com/blog/now-ga-share-materialized-views-and-streaming-tables-delta-sharing).

Providers can share live Materialized Views (precomputed aggregates — share insights instead of
full raw datasets, improving security and relevance) and Streaming Tables (continuous real-time
ingestion — ideal for operational dashboards, live inventory, IoT) over the open Delta Sharing
protocol, across clouds, regions, and platforms. GA additions:
- Providers can share custom views built on top of an MV/ST, and use column mapping to rename or
  hide columns without data rewrites.
- Recipients can create views on shared MV/STs, build their own MV/ST pipelines on top, and
  join or union multiple shared MV/STs (or combine shared with local MV/STs).

**How this affects recommendations:**
- `freshness_requirement` is real-time or near real-time → suggest sharing a **Streaming Table**
  so the consumer gets always-fresh data without duplicate pipelines.
- Consumer needs only filtered/summarized results (esp. with PII concerns) → suggest sharing a
  **Materialized View** of aggregates rather than raw tables, optionally with column mapping.

### Collaboration modalities beyond direct table sharing
Source: Databricks, "What's New with Data Sharing and Collaboration - Summer 2025"
(https://www.databricks.com/blog/whats-new-data-sharing-and-collaboration-summer-2025) and the
OpenSharing blogs above. Content was rephrased for compliance with licensing restrictions.

Direct table sharing (Decision 1) is one of several first-class collaboration modalities. The
advisor selects among them in Decision 0:
- **Databricks Clean Rooms** — privacy-centric collaboration powered by Delta Sharing where no
  party exposes raw data. GA on AWS, Azure, and GCP. Supports multi-party rooms (up to 10 orgs),
  in-place privacy-centric identity resolution (link entities without exposing raw PII to a
  third party), and self-run notebooks (collaborators run their own notebooks with explicit
  approval). Best fit when raw-data exposure is not acceptable, especially PII + external.
- **Databricks Marketplace** — an open platform to publish data and AI-asset products to many or
  unknown consumers via Delta Sharing, with live no-copy access. Choose it over per-recipient
  RECIPIENTs for broad audiences or a listing/monetization path.
- **AI-asset sharing (OpenSharing)** — share models, agents/Agent Skills, and unstructured files
  zero-copy over the open protocol; **Genie Agent Sharing (Beta)** shares conversational,
  natural-language access to data instead of raw tables.
- **OIDC Token Federation (GA)** — share with non-Databricks recipients who authenticate via
  their own IdP (Azure Entra ID, Okta, etc.) instead of long-lived tokens.
- **Delta Sharing Network Gateway (Public Preview)** — lets recipients access the source live
  with minimal manual firewall/network configuration (customer-managed S3/ADLS or Databricks
  default storage).

### Apache Iceberg v3 — GA on Unity Catalog
Source: Databricks, "The next era of the open lakehouse: Apache Iceberg™ v3" and "Advancing
Apache Iceberg on Databricks: Iceberg v3 GA, Open Sharing, and Unified Governance"
(https://www.databricks.com/blog/unity-catalog-and-next-era-apache-icebergtm). Content was
rephrased for compliance with licensing restrictions.

Iceberg v3 features are native on Unity Catalog managed, foreign, and UniForm-enabled tables,
and matter for *what format to share*:
- **Row lineage** — every row carries a permanent row ID and a sequence number marking when it
  last changed, so downstream consumers can identify changed rows without full scans.
- **Deletion vectors** — logical deletes tracked in lightweight delete files instead of
  rewriting Parquet, making change application markedly faster than copy-on-write.
- **VARIANT** — a native semi-structured column type that stores logs/API/clickstream/IoT
  payloads alongside relational columns in one table, queryable with standard SQL and with no
  schema migration when new fields appear.
- **UniForm + v3** — write once to Delta and read as Iceberg from Snowflake, BigQuery, Redshift,
  Athena, Trino, or any Iceberg engine, now without giving up Delta's performance features.

**How this affects recommendations (Decision 1c):**
- Cross-engine CDC to a non-Databricks consumer → recommend **managed Iceberg v3** (row lineage +
  deletion vectors) rather than relying on Delta `WITH HISTORY`.
- Semi-structured data → recommend **VARIANT** so the payload ships in one governed table.
- Delta source + Iceberg-reading consumer (e.g. Snowflake, Trino) → recommend **UniForm** to
  avoid a replication pipeline.

## MCP Config Placeholders

Before using the Confluence integration, replace the placeholders in `mcp.json` with your
values and provide an API token via environment variable.

- **`YOUR_ATLASSIAN_SITE_NAME`**: Your Atlassian site/subdomain — the part before
  `.atlassian.net` (e.g. for `https://acme.atlassian.net` the value is `acme`).
  - **How to get it:** It's in your Confluence/Jira URL. Use just the subdomain, not the full URL.

- **`YOUR_ATLASSIAN_USER_EMAIL`**: The email address of the Atlassian account the API token
  belongs to.
  - **How to set it:** Use the email you log in to Atlassian with.

- **`${ATLASSIAN_API_TOKEN}`**: An Atlassian API token, read from the `ATLASSIAN_API_TOKEN`
  environment variable (do not hardcode the token in the file).
  - **How to get it:**
    1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
    2. Click "Create API token", give it a label, and copy the value
    3. Export it in your shell before launching Kiro:
       `export ATLASSIAN_API_TOKEN="your-token-here"`

**After replacing placeholders, your `mcp.json` env block should look like:**
```json
"env": {
  "ATLASSIAN_SITE_NAME": "acme",
  "ATLASSIAN_USER_EMAIL": "you@example.com",
  "ATLASSIAN_API_TOKEN": "${ATLASSIAN_API_TOKEN}"
}
```

**Note:** You already have this server configured in `~/.kiro/settings/mcp.json` (under
`powers.mcpServers.atlassian-confluence`, site `certificationmaniox`) but it is currently
`disabled: true`. Enable it (and export `ATLASSIAN_API_TOKEN`) to use the integration — see the
testing steps.

---

**Knowledge base:** Databricks data-sharing architecture decision logic (+ Unity Catalog Iceberg)
**MCP Server:** atlassian-confluence (`@aashari/mcp-server-atlassian-confluence`)

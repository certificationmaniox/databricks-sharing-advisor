# Databricks Sharing Architecture Advisor (Kiro Power)

A Kiro Power that recommends the right architecture for sharing Databricks data with a
consumer. Given a scenario (metastore/account/region topology, consumer platform, identity,
data characteristics, freshness, security, and compliance needs), it walks a deterministic
decision tree and produces the primary and secondary solution, prerequisites, security
measures, cost considerations, step-by-step implementation, ready-to-run SQL/code, and an
architecture diagram.

> This project is not affiliated with or endorsed by Databricks. Product and platform names are
> the property of their respective owners.

## Contents

| Path | Purpose |
|------|---------|
| `POWER.md` | The power definition: overview, discovery questions, decision tree, solution catalog, SQL/code templates, diagrams. |
| `steering/` | Reference guides for each sharing solution. |
| `icon.png`, `icon.svg` | Power icon. |

## Solutions covered

- Direct GRANT + cross-catalog views (same metastore)
- Databricks-to-Databricks Delta Sharing
- Delta Sharing to Snowflake / Power BI / Python / Spark
- Unity Catalog Iceberg REST sharing (managed & foreign Iceberg, UniForm)
- JDBC/ODBC over a Databricks SQL warehouse
- Shared S3 external location (read-write)


## Security notes

- Never commit a real API token. `mcp.json` references `${ATLASSIAN_API_TOKEN}`.
- `ATLASSIAN_USER_EMAIL` is a placeholder in this repo; set your real value locally.
- Treat all generated SQL as a starting template — replace catalog/schema/table names, sharing
  IDs, and credentials with real values before running.

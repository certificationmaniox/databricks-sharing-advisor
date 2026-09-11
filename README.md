# Databricks Sharing Architecture Advisor (Kiro Power)

A Kiro Power that recommends the right architecture for sharing Databricks data with a
consumer. Given a scenario (metastore/account/region topology, consumer platform, identity,
data characteristics, freshness, security, and compliance needs), it walks a deterministic
decision tree and produces the primary and secondary solution, prerequisites, security
measures, cost considerations, step-by-step implementation, ready-to-run SQL/code, and an
architecture diagram.

It is a knowledge-base power: the recommendation is reasoning over documented rules, not code
execution. It also ships an optional Atlassian Confluence integration so a recommendation can
be published as durable team documentation.

> This project is not affiliated with or endorsed by Databricks. Product and platform names are
> the property of their respective owners.

## Contents

| Path | Purpose |
|------|---------|
| `POWER.md` | The power definition: overview, discovery questions, decision tree, solution catalog, SQL/code templates, diagrams. |
| `mcp.json` | MCP server config for the optional Atlassian Confluence integration. |
| `steering/` | Reference guides for each sharing solution. |
| `icon.png`, `icon.svg` | Power icon. |

## Solutions covered

- Direct GRANT + cross-catalog views (same metastore)
- Databricks-to-Databricks Delta Sharing
- Delta Sharing to Snowflake / Power BI / Python / Spark
- Unity Catalog Iceberg REST sharing (managed & foreign Iceberg, UniForm)
- JDBC/ODBC over a Databricks SQL warehouse
- Shared S3 external location (read-write)

## Confluence integration setup

The Confluence integration reads its API token from an environment variable so the token never
lives in a committed file. Configure it once:

1. Create an Atlassian API token at
   <https://id.atlassian.com/manage-profile/security/api-tokens>.
2. Export it in your shell (e.g. `~/.zshrc`):
   ```bash
   export ATLASSIAN_API_TOKEN="<your-token>"
   ```
3. In `mcp.json`, set `ATLASSIAN_SITE_NAME` (your Atlassian subdomain) and
   `ATLASSIAN_USER_EMAIL` (your login email). Leave `ATLASSIAN_API_TOKEN` as
   `${ATLASSIAN_API_TOKEN}`.
4. Reconnect / restart the MCP server so it picks up the environment variable.

To rotate the token later, update only the one line in your shell profile and restart — no
config edits.

## Security notes

- Never commit a real API token. `mcp.json` references `${ATLASSIAN_API_TOKEN}`.
- `ATLASSIAN_USER_EMAIL` is a placeholder in this repo; set your real value locally.
- Treat all generated SQL as a starting template — replace catalog/schema/table names, sharing
  IDs, and credentials with real values before running.

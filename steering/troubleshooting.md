# Troubleshooting Sharing (Symptom → Cause → Fix)

**Read this when** the user reports a sharing failure or asks why sharing/consuming "doesn't
work." Most tickets are one of a handful of recurring causes — check the symptom first.

**Triage shortcut:** nine times out of ten it is (1) SCIM group membership not synced, (2) wrong
environment/region/workspace, or (3) a SQL warehouse that needs starting/provisioning. Check
those before deep-diving.

## Access and permissions

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `PERMISSION_DENIED` on SELECT | Group not SCIM-synced, or querying a non-output-port table | Confirm SCIM sync and that the service account is in the consumer group; only query gold output ports |
| 403 on file read despite SELECT | Missing `EXTERNAL USE LOCATION` on the external location | Grant `EXTERNAL USE LOCATION` to the consumer group (it is excluded from ALL PRIVILEGES) |
| Grant looks correct but can't traverse | Missing a rung of USE CATALOG → USE SCHEMA → SELECT | Grant all three, to the group (never an individual), at the narrowest object |
| Recipient can't mount the share | Wrong sharing ID | Use `SELECT current_metastore()` (the metastore UUID, not a workspace/account ID) |

## Compute and connectivity

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| SQL Warehouse unavailable | Warehouse stopped or not provisioned | Start it (Serverless cold start ~5–10s) |
| JDBC times out from consumer | No network route (no PrivateLink) | Configure PrivateLink or VPC peering |
| `401 / invalid_client` on connect | Bad/expired SP secret or wrong OAuth URI | Rotate the secret; verify `OAUTH_TOKEN_URI`; use OAuth M2M |
| Cross-region read is slow | Different regions | Expect ~$0.01–0.02/GB egress; replicate hot data or filter the share |

## Data correctness and governance

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Stale data after upstream change | UniForm metadata is async; no REFRESH | Run `ALTER ICEBERG TABLE … REFRESH`; schedule to match SLA |
| No `iceberg.metadata.location` | UniForm/CompatV2 not enabled, or deletion vectors ON | Set `enableIcebergCompatV2=true`, `enableDeletionVectors=false`; `REORG … PURGE` then `OPTIMIZE`. (Managed Iceberg v3 keeps DV on — this fix is only for the UniForm/CompatV2 path.) |
| Masks not applied on consumer | Used open-protocol sharing or DEEP CLONE | Use D2D or Federation (both enforce masks), or pre-mask a view |
| PII appears where it shouldn't | Raw sensitive data on the wrong path | Share only anonymized/non-PII gold; route sensitive combined compute to a Clean Room |

Source for the UniForm/deletion-vectors interaction: Databricks docs, "Read Delta Lake tables
with Iceberg clients using UniForm" and "Deletion vectors in Databricks" / "Use Apache Iceberg v3
features." Content was rephrased for compliance with licensing restrictions.

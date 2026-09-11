# Solution: SHARED_EXTERNAL_LOCATION

**Read this when** Decision 1 selects `SHARED_EXTERNAL_LOCATION` (i.e. `access_type` ==
"Read-write"). Secondary: Reverse ETL Pipeline.

> Iceberg note: Managed Iceberg on Unity Catalog is read-write from any engine via the UC
> Iceberg REST Catalog API. If both sides can speak Iceberg REST, prefer `ICEBERG_REST_SHARING`
> (see iceberg-rest-sharing.md) over a raw shared S3 location for governed writes.

| Field | Value |
|-------|-------|
| Name | Shared S3 External Location |
| Description | Both parties access same S3 path via separate IAM roles. Supports read-write. |
| Complexity | High |
| Latency | Depends on write frequency |
| Cost | S3 storage + IAM management overhead |

## Implementation Steps
1. Create shared S3 bucket (or path) accessible by both parties
2. Create IAM role for provider (read+write)
3. Create IAM role for consumer (read-only or read-write)
4. Provider: `CREATE EXTERNAL LOCATION` pointing to S3 path
5. Consumer: `CREATE EXTERNAL LOCATION` with their IAM role
6. Consumer: `CREATE TABLE ... LOCATION 's3://shared-bucket/path/'`
7. Both: set up access via Unity Catalog storage credentials
8. Manage via Terraform for consistency

## Generated SQL
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

## Architecture Diagram
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

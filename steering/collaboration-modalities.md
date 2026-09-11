# Collaboration Modalities (Clean Rooms, Marketplace, AI-Asset Sharing)

**Read this when** Decision 0 resolves to `CLEAN_ROOMS`, `MARKETPLACE`, or `AI_ASSET_SHARING`
(i.e. the scenario is not plain direct table sharing), or the user asks about privacy-centric
collaboration, publishing a data product broadly, or sharing models/agents/unstructured data.

Direct table sharing (Decision 1) is one of several first-class Databricks collaboration
modalities. Decision 0 picks the modality first; if it is not `TABLE_SHARING`, lead with the
matching section below as the primary recommendation and use the Decision 1 catalog/SQL/diagram
only for any supporting tabular data.

Sources: Databricks, "What's New with Data Sharing and Collaboration - Summer 2025"
(https://www.databricks.com/blog/whats-new-data-sharing-and-collaboration-summer-2025) and the
OpenSharing blogs
(https://www.databricks.com/blog/announcing-new-opensharing-and-marketplace-capabilities-ai-era,
https://www.databricks.com/blog/introducing-opensharing-next-evolution-delta-sharing-agentic-era).
Content was rephrased for compliance with licensing restrictions.

## CLEAN_ROOMS — privacy-centric collaboration

**Selected when** `raw_data_exposure_ok` == "No (compute on joined data only)" OR
`collaboration_intent` == "Joint analysis without exposing raw data". Strongly prefer over table
sharing when `contains_pii` == "Yes" AND `consumer_external` == "Yes" — it replaces the "don't
share PII externally" dead-end with a workable path.

| Field | Value |
|-------|-------|
| Name | Databricks Clean Rooms |
| Description | Privacy-centric collaboration (powered by Delta Sharing) where no party exposes raw data; parties run approved queries/notebooks on joined data. |
| Complexity | Medium |
| Latency | On-demand (collaborators run approved jobs) |
| Cost | Consumer/collaborator compute; no raw-data copy |

Key capabilities (2025):
- **Any cloud** — GA on AWS, Azure, and GCP; collaborators can be on different clouds/regions.
- **Multi-party** — up to 10 organizations in one room (previously two-party only), with
  fine-grained access controls and orchestration.
- **Privacy-centric identity resolution** — link entities across datasets in place, without
  exposing raw PII to a third-party identity provider.
- **Run your own notebooks** — collaborators upload and run their own notebooks, only with
  explicit approval from the other participants.

### Implementation Steps
1. Create a clean room and invite the collaborator org(s) (up to 10 total).
2. Each party adds the datasets they contribute (shared in place via Delta Sharing; raw rows are
   not exposed to the other side).
3. If joining on people/accounts, enable privacy-centric identity resolution rather than
   exchanging raw identifiers.
4. Author or approve the notebooks/queries allowed to run; run-your-own-notebook requires
   explicit approval from other participants.
5. Run the approved analysis; only the permitted outputs are returned to each party.
6. Enable audit logging and review outputs before release when data is Confidential/Restricted.

### Architecture Diagram
```
┌──────────────────┐        ┌───────────────────────────┐        ┌──────────────────┐
│  PARTY A         │        │   DATABRICKS CLEAN ROOM   │        │  PARTY B         │
│  raw data (in    │──────► │   approved notebooks/     │ ◄──────│  raw data (in    │
│  place, unseen)  │ Delta  │   queries on joined data  │ Delta  │  place, unseen)  │
└──────────────────┘Sharing │   + identity resolution   │Sharing └──────────────────┘
                            │   up to 10 orgs, any cloud│
                            └───────────────────────────┘
  No party sees the other's raw rows; only approved outputs leave the room.
```

## MARKETPLACE — publish to many/unknown consumers

**Selected when** `collaboration_intent` == "Publish to many/unknown consumers" OR
`recipient_count` == "Many / broad audience". For a small set of named recipients, use table
sharing (Decision 1) instead.

| Field | Value |
|-------|-------|
| Name | Databricks Marketplace |
| Description | Open platform to publish a data (or AI-asset) product to many/unknown consumers via Delta Sharing; recipients get live, no-copy access. |
| Complexity | Medium |
| Latency | On-demand (recipients query the shared listing live) |
| Cost | S3 egress on reads; no per-recipient RECIPIENT management; optional monetization |

Use it over per-recipient RECIPIENTs when the audience is broad or you want a listing or
monetization path. The listing is backed by Delta Sharing, so the same read-only, no-copy
semantics apply. Governance still lives in Unity Catalog on the provider side.

### Implementation Steps
1. Prepare the data (or AI-asset) product: the tables/MV/model you want to list, governed in UC.
2. Create a provider profile and a Marketplace listing (public or private/targeted).
3. Attach the share (Delta Sharing) that backs the listing; add tables/MV/ST as usual.
4. Set listing metadata, terms, and (if applicable) monetization.
5. Publish; consumers request/subscribe and get live no-copy access via Delta Sharing.
6. Monitor usage and audit access; iterate on the listing contents like any shared object.

### Architecture Diagram
```
┌───────────────────────────┐   list    ┌───────────────────────────────┐
│  DATABRICKS (Provider)    │──────────►│  DATABRICKS MARKETPLACE       │
│  UC-governed product      │  Delta    │  public or private listing    │
│  (tables / MV / model)    │  Sharing  │                               │
└───────────────────────────┘           └───────────────┬───────────────┘
                                                         │ subscribe
                                     live, no-copy reads ▼
                              ┌────────────────────────────────────────┐
                              │  Many / unknown consumers (any platform)│
                              └────────────────────────────────────────┘
```

## AI_ASSET_SHARING — models, agents, unstructured data (OpenSharing)

**Selected when** `shared_asset_kind` in {"AI model", "Agent / Agent Skill", "Unstructured
files"} OR `collaboration_intent` implies sharing models/agents. After recommending the modality,
still run Decision 1 for any tabular data the asset depends on.

| Field | Value |
|-------|-------|
| Name | AI-asset sharing (OpenSharing) |
| Description | Zero-copy sharing of AI assets — models, agents/Agent Skills, unstructured files — over the open, vendor-neutral OpenSharing protocol (the evolution of Delta Sharing, now a Linux Foundation project). |
| Complexity | Medium |
| Latency | On-demand |
| Cost | Egress on reads; consumer compute for model/agent use |

Key points:
- **OpenSharing** extends zero-copy sharing beyond tables to the full AI stack across any cloud,
  vendor, and format.
- **Genie Agent Sharing (Beta)** — share conversational, natural-language access to your data
  with external partners instead of raw tables. Recommend this when the consumer wants a
  question-answering interface over the data rather than the rows themselves.
- **Unstructured files** — share file assets zero-copy alongside tabular data.

### Implementation Steps
1. Identify the asset kind: model, agent/Agent Skill, unstructured files, or a Genie space.
2. Register/govern the asset in Unity Catalog (models and other assets are UC-governed).
3. Create a share and add the asset; create a RECIPIENT (or Marketplace listing for broad reach).
4. For conversational access, share a Genie space via Genie Agent Sharing (Beta) rather than the
   underlying tables.
5. Send the activation link / OIDC-federated access to the consumer.
6. For any tables the model/agent reads, run Decision 1 and apply that solution to the tabular
   portion.

### Architecture Diagram
```
┌───────────────────────────┐  OpenSharing ┌──────────────────────────────┐
│  DATABRICKS (Provider)    │  (open,      │  Consumer / partner          │
│  UC-governed AI assets:   │  vendor-     │  uses model / agent / files  │
│  model / agent / files    │──neutral)───►│  or asks Genie in natural    │
│  + Genie space (Beta)     │  zero-copy   │  language (Beta)             │
└───────────────────────────┘  any cloud   └──────────────────────────────┘
  Supporting tables shared separately via Decision 1.
```

## Cross-cutting: auth and networking for external recipients

Applies to any modality with an external, non-Databricks recipient:
- **OIDC Token Federation (GA)** — let the recipient authenticate via their own IdP (Azure Entra
  ID, Okta, etc.) instead of long-lived bearer tokens in a `.share` profile.
- **Delta Sharing Network Gateway (Public Preview)** — give recipients live access to the source
  with minimal manual firewall/network configuration (customer-managed S3/ADLS or Databricks
  default storage).
- **SecureConnect (Public Preview)** / **Global Distribution (Private Preview)** — one-click
  cross-cloud connectivity and automatic cross-region/cross-cloud replication to cut egress.
- **Cross-regulatory-domain sharing (Public Preview)** — share across boundaries like GovCloud
  and commercial clouds instead of building a manual replica.

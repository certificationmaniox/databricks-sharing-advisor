# Databricks notebook source
# MAGIC %md
# MAGIC # 11 - Data Sharing Architecture Advisor (Interactive)
# MAGIC 
# MAGIC This interactive notebook asks discovery questions and recommends the best
# MAGIC data sharing architecture for your specific scenario.
# MAGIC 
# MAGIC **How to use:**
# MAGIC 1. Fill in the widget parameters at the top (click the widget bar)
# MAGIC 2. Run all cells
# MAGIC 3. Get your recommended architecture + implementation code
# MAGIC 
# MAGIC Covers all combinations: same/different metastore, same/different account,
# MAGIC internal/external consumers, Databricks/Snowflake/Power BI/Python targets.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Answer the Discovery Questions
# MAGIC 
# MAGIC Fill in the widgets above (or use the dropdowns). Then run the next cells.

# COMMAND ----------

# Section 1: Environment
class _WidgetFallback:
    def __init__(self):
        self._values = {}

    def dropdown(self, name, default, choices, label=None):
        value = self._prompt(name, default, choices, label)
        self._values[name] = value
        return value

    def text(self, name, default, label=None):
        value = self._prompt(name, default, None, label)
        self._values[name] = value
        return value

    def get(self, name):
        return self._values.get(name)

    def _prompt(self, name, default, choices, label):
        prompt = f"{label or name} [{default}]"
        if choices:
            prompt += f" (options: {', '.join(choices)})"
        value = input(prompt + ": ").strip()
        return value if value else default

try:
    dbutils_obj = globals().get("dbutils")
    if dbutils_obj is None or not hasattr(dbutils_obj, "widgets"):
        raise NameError("dbutils is not available")
    dbutils = dbutils_obj
except Exception:
    class _DbUtilsFallback:
        def __init__(self):
            self.widgets = _WidgetFallback()

    dbutils = _DbUtilsFallback()

dbutils.widgets.dropdown("same_metastore", "No", ["Yes", "No"], "1.1 Same Metastore?")
dbutils.widgets.dropdown("same_account", "Yes", ["Yes", "No"], "1.2 Same Databricks Account?")
dbutils.widgets.dropdown("same_region", "Yes", ["Yes", "No"], "1.3 Same AWS Region?")

dbutils.widgets.dropdown("consumer_platform", "Databricks", 
    ["Databricks", "Snowflake", "Power BI", "Python/Pandas", "Spark (non-Databricks)", "dbt", "Other"],
    "1.4 Consumer Platform?")
dbutils.widgets.text("provider_region", "us-east-1", "1.5 Provider AWS Region")
dbutils.widgets.text("consumer_region", "us-east-1", "1.6 Consumer AWS Region")

# Section 2: Identity & Access
dbutils.widgets.dropdown("consumer_identity", "Service Principal", 
    ["Human Users", "Service Principal", "External Application", "Partner Organization"],
    "2.1 Consumer Identity Type?")
dbutils.widgets.dropdown("access_type", "Read-only", 
    ["Read-only", "Read-write"],
    "2.2 Access Type Needed?")
dbutils.widgets.dropdown("groups_exist", "No", ["Yes", "No"], "2.3 Account-Level Groups Exist?")

# Section 3: Data Characteristics
dbutils.widgets.dropdown("data_volume", "Medium (1-100 GB)", 
    ["Small (< 1 GB)", "Medium (1-100 GB)", "Large (100 GB - 1 TB)", "Very Large (> 1 TB)"],
    "3.1 Data Volume?")
dbutils.widgets.dropdown("contains_pii", "No", ["Yes", "No"], "3.2 Contains PII?")
dbutils.widgets.dropdown("data_classification", "Internal", 
    ["Public", "Internal", "Confidential", "Restricted"],
    "3.3 Data Classification?")
dbutils.widgets.dropdown("needs_cdc", "No", ["Yes", "No"], "3.4 Needs Change Data Feed (CDC)?")

# Section 4: Freshness & SLA
dbutils.widgets.dropdown("freshness_requirement", "Daily", 
    ["Real-time (< 1 min)", "Near real-time (< 15 min)", "Hourly", "Daily", "Weekly"],
    "4.1 Freshness Requirement?")
dbutils.widgets.dropdown("sharing_duration", "Ongoing", 
    ["One-time export", "Ongoing (continuous)", "Time-limited (project)"],
    "4.2 Sharing Duration?")

# Section 5: Security & Compliance
dbutils.widgets.dropdown("data_residency", "No restriction", 
    ["No restriction", "Must stay in same region", "Must stay in same country", "Must stay in same account"],
    "5.1 Data Residency Requirement?")
dbutils.widgets.dropdown("needs_column_security", "No", ["Yes", "No"], "5.2 Column-Level Security?")
dbutils.widgets.dropdown("needs_row_security", "No", ["Yes", "No"], "5.3 Row-Level Security?")
dbutils.widgets.dropdown("consumer_external", "No", ["Yes", "No"], "5.4 Consumer External to Org?")

# Section 6: Consumer needs
dbutils.widgets.dropdown("consumer_needs_transform", "No (read-only queries)", 
    ["No (read-only queries)", "Yes (build views/tables on top)", "Yes (ML/AI workloads)"],
    "6.1 Consumer Needs Transformation?")
dbutils.widgets.text("tables_to_share", "gold_products.*", "6.2 Tables to Share (schema.table)")
dbutils.widgets.text("consumer_name", "Finance Team", "6.3 Consumer Name/Team")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Run the Advisor Engine

# COMMAND ----------

# Collect all inputs
inputs = {
    "same_metastore": dbutils.widgets.get("same_metastore"),
    "same_account": dbutils.widgets.get("same_account"),
    "same_region": dbutils.widgets.get("same_region"),
    "consumer_platform": dbutils.widgets.get("consumer_platform"),
    "provider_region": dbutils.widgets.get("provider_region"),
    "consumer_region": dbutils.widgets.get("consumer_region"),
    "consumer_identity": dbutils.widgets.get("consumer_identity"),
    "access_type": dbutils.widgets.get("access_type"),
    "groups_exist": dbutils.widgets.get("groups_exist"),
    "data_volume": dbutils.widgets.get("data_volume"),
    "contains_pii": dbutils.widgets.get("contains_pii"),
    "data_classification": dbutils.widgets.get("data_classification"),
    "needs_cdc": dbutils.widgets.get("needs_cdc"),
    "freshness_requirement": dbutils.widgets.get("freshness_requirement"),
    "sharing_duration": dbutils.widgets.get("sharing_duration"),
    "data_residency": dbutils.widgets.get("data_residency"),
    "needs_column_security": dbutils.widgets.get("needs_column_security"),
    "needs_row_security": dbutils.widgets.get("needs_row_security"),
    "consumer_external": dbutils.widgets.get("consumer_external"),
    "consumer_needs_transform": dbutils.widgets.get("consumer_needs_transform"),
    "tables_to_share": dbutils.widgets.get("tables_to_share"),
    "consumer_name": dbutils.widgets.get("consumer_name"),
}

print("Inputs collected. Running advisor engine...")

# COMMAND ----------

# ═══════════════════════════════════════════════════════════════
# DECISION ENGINE
# ═══════════════════════════════════════════════════════════════

def recommend_architecture(inputs):
    """Analyze inputs and recommend the best sharing architecture."""
    
    recommendations = {
        "primary_solution": "",
        "secondary_solution": "",
        "prerequisites": [],
        "security_measures": [],
        "cost_considerations": [],
        "warnings": [],
        "implementation_steps": [],
    }
    
    # ─── DECISION 1: Determine primary sharing method ───
    
    if inputs["access_type"] == "Read-write":
        recommendations["primary_solution"] = "SHARED_EXTERNAL_LOCATION"
        recommendations["secondary_solution"] = "Reverse ETL Pipeline"
        recommendations["warnings"].append(
            "Delta Sharing is READ-ONLY. For write access, use shared S3 external locations with IAM roles."
        )
    elif inputs["same_metastore"] == "Yes":
        recommendations["primary_solution"] = "DIRECT_GRANT_WITH_VIEWS"
        recommendations["secondary_solution"] = "Cross-Catalog Views"
    elif inputs["consumer_platform"] == "Databricks":
        recommendations["primary_solution"] = "DATABRICKS_TO_DATABRICKS_SHARING"
        recommendations["secondary_solution"] = "Shared S3 External Location"
    elif inputs["consumer_platform"] == "Snowflake":
        recommendations["primary_solution"] = "DELTA_SHARING_SNOWFLAKE"
        recommendations["secondary_solution"] = "S3 Export + Snowpipe"
    elif inputs["consumer_platform"] == "Power BI":
        recommendations["primary_solution"] = "DELTA_SHARING_POWER_BI"
        recommendations["secondary_solution"] = "Databricks SQL Direct Connect"
    elif inputs["consumer_platform"] in ["Python/Pandas", "Spark (non-Databricks)"]:
        recommendations["primary_solution"] = "DELTA_SHARING_OPEN_PROTOCOL"
        recommendations["secondary_solution"] = "S3 Direct Access with IAM"
    else:
        recommendations["primary_solution"] = "DELTA_SHARING_OPEN_PROTOCOL"
        recommendations["secondary_solution"] = "REST API Export"
    
    # ─── DECISION 2: Prerequisites ───
    
    if inputs["groups_exist"] == "No":
        recommendations["prerequisites"].append(
            "Create account-level groups in accounts.cloud.databricks.com (or via SCIM)"
        )
    
    if inputs["same_metastore"] == "No" and inputs["consumer_platform"] == "Databricks":
        recommendations["prerequisites"].append(
            "Exchange metastore sharing identifiers between provider and consumer"
        )
    
    if inputs["consumer_identity"] == "Service Principal":
        recommendations["prerequisites"].append(
            "Create service principal at account level + generate OAuth credentials"
        )
        recommendations["prerequisites"].append(
            "Add service principal to appropriate groups"
        )
    
    if inputs["consumer_external"] == "Yes":
        recommendations["prerequisites"].append(
            "Create RECIPIENT in Unity Catalog for external consumer"
        )
        recommendations["prerequisites"].append(
            "Generate and securely transmit activation link to consumer"
        )
    
    # ─── DECISION 3: Security measures ───
    
    if inputs["contains_pii"] == "Yes":
        recommendations["security_measures"].append(
            "Create dynamic views with column masking (is_account_group_member)"
        )
        recommendations["security_measures"].append(
            "Tag PII columns with 'pii=true' classification"
        )
        if inputs["consumer_external"] == "Yes":
            recommendations["security_measures"].append(
                "DO NOT share PII tables externally. Use anonymized/aggregated gold products only."
            )
            recommendations["warnings"].append(
                "⚠️  PII + External consumer = HIGH RISK. Share only aggregated/anonymized data."
            )
    
    if inputs["needs_column_security"] == "Yes":
        recommendations["security_measures"].append(
            "Create secure views with CASE WHEN is_account_group_member() logic"
        )
    
    if inputs["needs_row_security"] == "Yes":
        recommendations["security_measures"].append(
            "Create filtered views with row-level predicates based on group membership"
        )
        recommendations["security_measures"].append(
            "Or: Use partition-based sharing (share only relevant partitions)"
        )
    
    if inputs["data_classification"] in ["Confidential", "Restricted"]:
        recommendations["security_measures"].append(
            "Enable audit logging (system.access.audit)"
        )
        recommendations["security_measures"].append(
            "Require VPC PrivateLink for data access (no public internet)"
        )
        recommendations["security_measures"].append(
            "Review with security team before enabling sharing"
        )
    
    if inputs["data_residency"] != "No restriction":
        recommendations["warnings"].append(
            f"⚠️  Data residency: '{inputs['data_residency']}' — verify sharing doesn't violate this."
        )
        if inputs["same_region"] == "No":
            recommendations["warnings"].append(
                "⚠️  Cross-region sharing may violate data residency. Consider local replica or filtered share."
            )
    
    # ─── DECISION 4: Cost considerations ───
    
    if inputs["same_region"] == "No":
        recommendations["cost_considerations"].append(
            f"S3 cross-region egress: ~$0.02/GB ({inputs['provider_region']} → {inputs['consumer_region']})"
        )
        if inputs["data_volume"] in ["Large (100 GB - 1 TB)", "Very Large (> 1 TB)"]:
            recommendations["cost_considerations"].append(
                "HIGH VOLUME + CROSS-REGION: Consider S3 replication to consumer region to reduce egress"
            )
    
    if inputs["data_volume"] == "Very Large (> 1 TB)":
        recommendations["cost_considerations"].append(
            "Large dataset: ensure tables are partitioned for efficient predicate pushdown"
        )
    
    if inputs["freshness_requirement"] in ["Real-time (< 1 min)", "Near real-time (< 15 min)"]:
        recommendations["cost_considerations"].append(
            "Real-time freshness requires streaming pipeline (higher compute cost)"
        )
    
    recommendations["cost_considerations"].append(
        "Provider: Zero compute cost for Delta Sharing reads (no cluster involved)"
    )
    recommendations["cost_considerations"].append(
        "Consumer: Pays their own compute for query execution"
    )
    
    # ─── DECISION 5: Implementation steps ───
    
    solution = recommendations["primary_solution"]
    consumer = inputs["consumer_name"]
    tables = inputs["tables_to_share"]
    
    if solution == "DIRECT_GRANT_WITH_VIEWS":
        recommendations["implementation_steps"] = [
            f"1. Create account-level group for {consumer}",
            f"2. GRANT USE CATALOG ON CATALOG demo_sales TO `{consumer.lower().replace(' ', '_')}`",
            f"3. GRANT USE SCHEMA ON SCHEMA demo_sales.{tables.split('.')[0]} TO `{consumer.lower().replace(' ', '_')}`",
            f"4. GRANT SELECT ON TABLE/SCHEMA demo_sales.{tables} TO `{consumer.lower().replace(' ', '_')}`",
            f"5. Consumer creates views in their catalog referencing demo_sales tables",
            "6. Document in table comments + add tags",
            "7. Set up audit monitoring",
        ]
    elif solution == "DATABRICKS_TO_DATABRICKS_SHARING":
        recommendations["implementation_steps"] = [
            "1. Get consumer metastore sharing identifier (consumer runs: SELECT current_metastore())",
            "2. Provider: CREATE SHARE sales_share",
            f"3. Provider: ALTER SHARE sales_share ADD TABLE demo_sales.{tables}",
            f"4. Provider: CREATE RECIPIENT {consumer.lower().replace(' ', '_')} USING ID '<consumer-sharing-id>'",
            f"5. Provider: GRANT SELECT ON SHARE sales_share TO RECIPIENT {consumer.lower().replace(' ', '_')}",
            "6. Consumer: CREATE PROVIDER sales_provider USING ID '<provider-sharing-id>'",
            "7. Consumer: CREATE CATALOG sales_shared USING SHARE sales_provider.sales_share",
            "8. Consumer: GRANT USE CATALOG ON sales_shared TO their local groups",
            "9. Consumer: Query via SELECT * FROM sales_shared.gold_products.*",
        ]
    elif solution == "DELTA_SHARING_SNOWFLAKE":
        recommendations["implementation_steps"] = [
            "1. Provider: CREATE SHARE sales_share",
            f"2. Provider: ALTER SHARE sales_share ADD TABLE demo_sales.{tables}",
            "3. Provider: CREATE RECIPIENT snowflake_consumer",
            "4. Provider: GRANT SELECT ON SHARE ... TO RECIPIENT snowflake_consumer",
            "5. Send activation link to Snowflake admin",
            "6. Snowflake: CREATE CATALOG INTEGRATION ... DELTA_SHARING",
            "7. Snowflake: CREATE DATABASE FROM DELTA_SHARING_SHARE",
            "8. Snowflake: Query as native tables",
        ]
    elif solution == "DELTA_SHARING_POWER_BI":
        recommendations["implementation_steps"] = [
            "1. Provider: CREATE SHARE sales_share",
            f"2. Provider: ALTER SHARE sales_share ADD TABLE demo_sales.{tables}",
            "3. Provider: CREATE RECIPIENT powerbi_consumer",
            "4. Provider: GRANT SELECT ON SHARE ... TO RECIPIENT powerbi_consumer",
            "5. Download .share profile from activation link",
            "6. Power BI: Get Data → Delta Sharing connector",
            "7. Power BI: Paste sharing profile URL",
            "8. Power BI: Select tables and build visuals",
            "9. Set up scheduled refresh (Import mode) or DirectQuery",
        ]
    elif solution == "DELTA_SHARING_OPEN_PROTOCOL":
        recommendations["implementation_steps"] = [
            "1. Provider: CREATE SHARE sales_share",
            f"2. Provider: ALTER SHARE sales_share ADD TABLE demo_sales.{tables}",
            f"3. Provider: CREATE RECIPIENT {consumer.lower().replace(' ', '_')}",
            f"4. Provider: GRANT SELECT ON SHARE ... TO RECIPIENT {consumer.lower().replace(' ', '_')}",
            "5. Send activation link to consumer (they download .share profile)",
            "6. Consumer: pip install delta-sharing",
            "7. Consumer: delta_sharing.load_as_pandas('<profile>#share.schema.table')",
            "8. Consumer: Process data in their environment",
        ]
    elif solution == "SHARED_EXTERNAL_LOCATION":
        recommendations["implementation_steps"] = [
            "1. Create shared S3 bucket (or path) accessible by both parties",
            "2. Create IAM role for provider (read+write)",
            "3. Create IAM role for consumer (read-only or read-write)",
            "4. Provider: CREATE EXTERNAL LOCATION pointing to S3 path",
            "5. Consumer: CREATE EXTERNAL LOCATION with their IAM role",
            "6. Consumer: CREATE TABLE ... LOCATION 's3://shared-bucket/path/'",
            "7. Both: Set up access via Unity Catalog storage credentials",
            "8. Manage via Terraform for consistency",
        ]
    
    return recommendations

# Run the engine
result = recommend_architecture(inputs)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Your Recommended Architecture

# COMMAND ----------

# ═══════════════════════════════════════════════════════════════
# OUTPUT: Recommendation Report
# ═══════════════════════════════════════════════════════════════

solution_descriptions = {
    "DIRECT_GRANT_WITH_VIEWS": {
        "name": "Direct GRANT + Cross-Catalog Views",
        "description": "Same metastore — grant SELECT directly and consumer creates views in their catalog.",
        "complexity": "Low",
        "latency": "Zero (live read from same Delta tables)",
        "cost": "Zero additional (same S3, same region)",
    },
    "DATABRICKS_TO_DATABRICKS_SHARING": {
        "name": "Databricks-to-Databricks (D2D) Sharing",
        "description": "Different metastores but both Databricks — uses Delta Sharing with native catalog integration.",
        "complexity": "Medium",
        "latency": "Near zero (metadata auto-sync, live reads via pre-signed URLs)",
        "cost": "S3 egress if cross-region, zero compute for sharing",
    },
    "DELTA_SHARING_SNOWFLAKE": {
        "name": "Delta Sharing → Snowflake",
        "description": "Open protocol sharing to Snowflake — tables appear as native Snowflake external tables.",
        "complexity": "Medium",
        "latency": "Minutes (Snowflake refreshes on query)",
        "cost": "S3 egress + Snowflake compute on consumer side",
    },
    "DELTA_SHARING_POWER_BI": {
        "name": "Delta Sharing → Power BI",
        "description": "Share data to Power BI via Delta Sharing connector — Import or DirectQuery mode.",
        "complexity": "Low-Medium",
        "latency": "Scheduled refresh (Import) or real-time (DirectQuery)",
        "cost": "S3 egress + Power BI Pro/Premium license",
    },
    "DELTA_SHARING_OPEN_PROTOCOL": {
        "name": "Delta Sharing (Open Protocol)",
        "description": "Generic open protocol — works with Python, Spark, any Delta Sharing client.",
        "complexity": "Low-Medium",
        "latency": "On-demand (reads when consumer queries)",
        "cost": "S3 egress + consumer's compute",
    },
    "SHARED_EXTERNAL_LOCATION": {
        "name": "Shared S3 External Location",
        "description": "Both parties access same S3 path via separate IAM roles. Supports read-write.",
        "complexity": "High",
        "latency": "Depends on write frequency",
        "cost": "S3 storage + IAM management overhead",
    },
}

sol = solution_descriptions.get(result["primary_solution"], {})

print("=" * 80)
print(f"  RECOMMENDED ARCHITECTURE FOR: {inputs['consumer_name']}")
print("=" * 80)
print()
print(f"  Primary Solution:  {sol.get('name', result['primary_solution'])}")
print(f"  Description:       {sol.get('description', '')}")
print(f"  Complexity:        {sol.get('complexity', 'N/A')}")
print(f"  Data Latency:      {sol.get('latency', 'N/A')}")
print(f"  Cost Impact:       {sol.get('cost', 'N/A')}")
print(f"  Alternative:       {result['secondary_solution']}")
print()
print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Prerequisites

# COMMAND ----------

print("PREREQUISITES (Complete these first):")
print("-" * 60)
if result["prerequisites"]:
    for i, prereq in enumerate(result["prerequisites"], 1):
        print(f"  {i}. {prereq}")
else:
    print("  No special prerequisites. Ready to implement.")
print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Security Measures

# COMMAND ----------

print("SECURITY MEASURES:")
print("-" * 60)
if result["security_measures"]:
    for i, measure in enumerate(result["security_measures"], 1):
        print(f"  {i}. {measure}")
else:
    print("  Standard security (Unity Catalog default governance applies).")
print()

if result["warnings"]:
    print()
    print("⚠️  WARNINGS:")
    print("-" * 60)
    for warning in result["warnings"]:
        print(f"  {warning}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Cost Considerations

# COMMAND ----------

print("COST CONSIDERATIONS:")
print("-" * 60)
for i, cost in enumerate(result["cost_considerations"], 1):
    print(f"  {i}. {cost}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7: Implementation Steps

# COMMAND ----------

print("IMPLEMENTATION STEPS:")
print("-" * 60)
for step in result["implementation_steps"]:
    print(f"  {step}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 8: Generated Implementation Code

# COMMAND ----------

# Generate implementation SQL based on the recommendation
consumer_slug = inputs["consumer_name"].lower().replace(" ", "_").replace("-", "_")
tables = inputs["tables_to_share"]

print("=" * 80)
print("  GENERATED SQL — Copy and run in appropriate workspace")
print("=" * 80)
print()

if result["primary_solution"] == "DIRECT_GRANT_WITH_VIEWS":
    print("-- ═══════════════════════════════════════════")
    print("-- PROVIDER SIDE (run in provider workspace)")
    print("-- ═══════════════════════════════════════════")
    print()
    print(f"-- Step 1: Grant access to {inputs['consumer_name']}")
    print(f"GRANT USE CATALOG ON CATALOG demo_sales TO `{consumer_slug}`;")
    print(f"GRANT USE SCHEMA ON SCHEMA demo_sales.{tables.split('.')[0] if '.' in tables else 'gold_products'} TO `{consumer_slug}`;")
    print(f"GRANT SELECT ON SCHEMA demo_sales.{tables.split('.')[0] if '.' in tables else 'gold_products'} TO `{consumer_slug}`;")
    print()
    print("-- ═══════════════════════════════════════════")
    print("-- CONSUMER SIDE (run in consumer workspace)")
    print("-- ═══════════════════════════════════════════")
    print()
    print(f"-- Step 2: Create local catalog for {inputs['consumer_name']}")
    print(f"CREATE CATALOG IF NOT EXISTS {consumer_slug}_catalog;")
    print(f"CREATE SCHEMA IF NOT EXISTS {consumer_slug}_catalog.shared_products;")
    print()
    print(f"-- Step 3: Create views pointing to provider")
    print(f"CREATE OR REPLACE VIEW {consumer_slug}_catalog.shared_products.revenue")
    print(f"AS SELECT * FROM demo_sales.gold_products.revenue_dashboard;")
    print()
    print(f"CREATE OR REPLACE VIEW {consumer_slug}_catalog.shared_products.customers")
    print(f"AS SELECT * FROM demo_sales.gold_products.customer_segments;")
    print()
    print("-- Step 4: Verify")
    print(f"SELECT * FROM {consumer_slug}_catalog.shared_products.revenue LIMIT 5;")

elif result["primary_solution"] == "DATABRICKS_TO_DATABRICKS_SHARING":
    print("-- ═══════════════════════════════════════════")
    print("-- PROVIDER SIDE (run in provider workspace)")
    print("-- ═══════════════════════════════════════════")
    print()
    print("-- Step 1: Create share")
    print(f"CREATE SHARE IF NOT EXISTS {consumer_slug}_share")
    print(f"COMMENT 'Data products shared with {inputs['consumer_name']}';")
    print()
    print("-- Step 2: Add tables to share")
    print(f"ALTER SHARE {consumer_slug}_share ADD TABLE demo_sales.gold_products.revenue_dashboard;")
    print(f"ALTER SHARE {consumer_slug}_share ADD TABLE demo_sales.gold_products.customer_segments;")
    print(f"ALTER SHARE {consumer_slug}_share ADD TABLE demo_sales.gold_products.product_catalog_public;")
    print()
    print("-- Step 3: Create recipient (replace <SHARING_ID> with consumer's metastore sharing ID)")
    print(f"CREATE RECIPIENT IF NOT EXISTS {consumer_slug}")
    print(f"  USING ID '<CONSUMER_METASTORE_SHARING_ID>'")
    print(f"  COMMENT '{inputs['consumer_name']} workspace';")
    print()
    print("-- Step 4: Grant share to recipient")
    print(f"GRANT SELECT ON SHARE {consumer_slug}_share TO RECIPIENT {consumer_slug};")
    print()
    print("-- Verify")
    print(f"SHOW ALL IN SHARE {consumer_slug}_share;")
    print()
    print("-- ═══════════════════════════════════════════")
    print("-- CONSUMER SIDE (run in consumer workspace)")
    print("-- ═══════════════════════════════════════════")
    print()
    print("-- Step 5: Get your metastore sharing ID (send to provider)")
    print("SELECT current_metastore() AS my_sharing_id;")
    print()
    print("-- Step 6: Create provider reference (replace <SHARING_ID>)")
    print("CREATE PROVIDER IF NOT EXISTS sales_data_provider")
    print("  USING ID '<PROVIDER_METASTORE_SHARING_ID>'")
    print("  COMMENT 'Sales domain data provider';")
    print()
    print("-- Step 7: See available shares")
    print("SHOW SHARES IN PROVIDER sales_data_provider;")
    print()
    print("-- Step 8: Create catalog from share")
    print("CREATE CATALOG IF NOT EXISTS sales_shared")
    print(f"  USING SHARE sales_data_provider.{consumer_slug}_share;")
    print()
    print("-- Step 9: Query!")
    print("SELECT * FROM sales_shared.gold_products.revenue_dashboard LIMIT 10;")
    print()
    print("-- Step 10: Grant to local users")
    print(f"GRANT USE CATALOG ON CATALOG sales_shared TO `{consumer_slug}`;")
    print(f"GRANT SELECT ON CATALOG sales_shared TO `{consumer_slug}`;")

elif result["primary_solution"] in ["DELTA_SHARING_SNOWFLAKE", "DELTA_SHARING_POWER_BI", "DELTA_SHARING_OPEN_PROTOCOL"]:
    print("-- ═══════════════════════════════════════════")
    print("-- PROVIDER SIDE (run in Databricks)")
    print("-- ═══════════════════════════════════════════")
    print()
    print("-- Step 1: Create share")
    print(f"CREATE SHARE IF NOT EXISTS {consumer_slug}_share")
    print(f"COMMENT 'Data products for {inputs['consumer_name']} ({inputs['consumer_platform']})';")
    print()
    print("-- Step 2: Add tables")
    print(f"ALTER SHARE {consumer_slug}_share ADD TABLE demo_sales.gold_products.revenue_dashboard;")
    print(f"ALTER SHARE {consumer_slug}_share ADD TABLE demo_sales.gold_products.customer_segments;")
    print(f"ALTER SHARE {consumer_slug}_share ADD TABLE demo_sales.gold_products.product_catalog_public;")
    print()
    if inputs["needs_cdc"] == "Yes":
        print("-- Step 2b: Enable change data feed on shared tables")
        print(f"ALTER SHARE {consumer_slug}_share ADD TABLE demo_sales.gold_products.revenue_dashboard")
        print("  WITH HISTORY;")
        print()
    print("-- Step 3: Create recipient")
    print(f"CREATE RECIPIENT IF NOT EXISTS {consumer_slug}")
    print(f"  COMMENT '{inputs['consumer_name']} - {inputs['consumer_platform']}';")
    print()
    print("-- Step 4: Grant share")
    print(f"GRANT SELECT ON SHARE {consumer_slug}_share TO RECIPIENT {consumer_slug};")
    print()
    print("-- Step 5: Get activation link (send to consumer)")
    print(f"-- Go to: Data Explorer → Delta Sharing → Recipients → {consumer_slug}")
    print("-- Click 'Activation Link' → copy and send securely to consumer")
    print()
    print(f"SHOW GRANTS TO RECIPIENT {consumer_slug};")
    print()
    print()
    print("-- ═══════════════════════════════════════════")
    print(f"-- CONSUMER SIDE ({inputs['consumer_platform']})")
    print("-- ═══════════════════════════════════════════")
    print()
    
    if inputs["consumer_platform"] == "Snowflake":
        print("-- In Snowflake:")
        print("CREATE OR REPLACE CATALOG INTEGRATION databricks_delta_share")
        print("  CATALOG_SOURCE = DELTA_SHARING")
        print("  TABLE_FORMAT = DELTA")
        print("  ENABLED = TRUE;")
        print()
        print("CREATE DATABASE IF NOT EXISTS sales_from_databricks")
        print("  FROM DELTA_SHARING_SHARE")
        print("  PROVIDER = 'databricks_provider'")
        print(f"  SHARE = '{consumer_slug}_share';")
        print()
        print("-- Query as native Snowflake tables:")
        print("SELECT * FROM sales_from_databricks.gold_products.revenue_dashboard;")
        
    elif inputs["consumer_platform"] == "Power BI":
        print("-- In Power BI Desktop:")
        print("-- 1. Get Data → More... → Delta Sharing")
        print("-- 2. Enter the sharing profile URL from activation link")
        print("-- 3. Select tables: revenue_dashboard, customer_segments")
        print("-- 4. Choose: Import (scheduled refresh) or DirectQuery (live)")
        print("-- 5. Build your visuals")
        print("-- 6. Publish to Power BI Service")
        print("-- 7. Set scheduled refresh (recommended: daily)")
        
    else:  # Python/Pandas or Spark
        print("# pip install delta-sharing")
        print()
        print("import delta_sharing")
        print()
        print('# Profile file from activation link')
        print('PROFILE = "/path/to/downloaded/config.share"')
        print()
        print("# List available tables")
        print("client = delta_sharing.SharingClient(PROFILE)")
        print("tables = client.list_all_tables()")
        print("for t in tables:")
        print('    print(f"  {t.share}.{t.schema}.{t.name}")')
        print()
        print("# Load as Pandas DataFrame")
        print(f'df = delta_sharing.load_as_pandas(')
        print(f'    f"{{PROFILE}}#{consumer_slug}_share.gold_products.revenue_dashboard"')
        print(f')')
        print()
        print("print(f'Loaded {len(df)} rows')")
        print("print(df.head())")
        print()
        print("# For Spark (non-Databricks):")
        print(f'spark_df = delta_sharing.load_as_spark(')
        print(f'    f"{{PROFILE}}#{consumer_slug}_share.gold_products.customer_segments"')
        print(f')')

elif result["primary_solution"] == "SHARED_EXTERNAL_LOCATION":
    print("-- ═══════════════════════════════════════════")
    print("-- SHARED S3 EXTERNAL LOCATION (Read-Write)")
    print("-- ═══════════════════════════════════════════")
    print()
    print("-- Step 1: Create shared S3 bucket/path")
    print("-- s3://shared-data-exchange/sales-to-finance/")
    print()
    print("-- Step 2: Provider IAM role (write access)")
    print("-- Trust: Databricks Unity Catalog role")
    print("-- Policy: s3:GetObject, s3:PutObject, s3:DeleteObject, s3:ListBucket")
    print()
    print("-- Step 3: Consumer IAM role (read or read-write)")
    print("-- Trust: Consumer's Databricks Unity Catalog role")
    print("-- Policy: s3:GetObject, s3:ListBucket (+ PutObject if write needed)")
    print()
    print("-- Step 4: Register in both workspaces")
    print("-- Provider workspace:")
    print("CREATE STORAGE CREDENTIAL IF NOT EXISTS provider_shared_cred")
    print("  WITH (AWS_IAM_ROLE = 'arn:aws:iam::PROVIDER_ACCOUNT:role/shared-write-role');")
    print()
    print("CREATE EXTERNAL LOCATION IF NOT EXISTS shared_exchange")
    print("  URL 's3://shared-data-exchange/sales-to-finance/'")
    print("  WITH (STORAGE CREDENTIAL provider_shared_cred);")
    print()
    print("-- Consumer workspace:")
    print("CREATE STORAGE CREDENTIAL IF NOT EXISTS consumer_shared_cred")
    print("  WITH (AWS_IAM_ROLE = 'arn:aws:iam::CONSUMER_ACCOUNT:role/shared-read-role');")
    print()
    print("CREATE EXTERNAL LOCATION IF NOT EXISTS shared_exchange")
    print("  URL 's3://shared-data-exchange/sales-to-finance/'")
    print("  WITH (STORAGE CREDENTIAL consumer_shared_cred);")
    print()
    print("-- Step 5: Consumer reads the data")
    print(f"CREATE TABLE IF NOT EXISTS {consumer_slug}_catalog.shared.revenue")
    print("  USING DELTA")
    print("  LOCATION 's3://shared-data-exchange/sales-to-finance/revenue_dashboard';")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 9: Architecture Diagram

# COMMAND ----------

# Visual architecture diagram
solution = result["primary_solution"]
consumer = inputs["consumer_name"]
platform = inputs["consumer_platform"]

print()
if solution == "DIRECT_GRANT_WITH_VIEWS":
    print(f"""
┌─────────────────────────────────────────────────────────────────┐
│                    SAME METASTORE                                 │
│                                                                  │
│  ┌──────────────────┐         ┌──────────────────────────────┐  │
│  │  demo_sales      │  GRANT  │  {consumer_slug}_catalog     │  │
│  │  gold_products   │────────►│  shared_products (VIEWS)     │  │
│  │  (Delta tables)  │ SELECT  │  → revenue, customers, etc.  │  │
│  └──────────────────┘         └──────────────────────────────┘  │
│                                                                  │
│  Data: Same S3, same region, zero copy, zero latency             │
│  Auth: GRANT to account-level group                              │
│  Cost: Zero additional                                           │
└─────────────────────────────────────────────────────────────────┘
""")

elif solution == "DATABRICKS_TO_DATABRICKS_SHARING":
    print(f"""
┌───────────────────────────┐           ┌───────────────────────────┐
│  PROVIDER WORKSPACE       │           │  CONSUMER WORKSPACE       │
│  ({inputs['provider_region']})         │           │  ({inputs['consumer_region']})         │
│                           │           │                           │
│  Metastore A              │  Delta    │  Metastore B              │
│  demo_sales.gold_products │  Sharing  │  sales_shared (CATALOG)   │
│  ├── revenue_dashboard    │──────────►│  ├── revenue_dashboard    │
│  ├── customer_segments    │  (D2D)    │  ├── customer_segments    │
│  └── product_catalog      │           │  └── product_catalog      │
│                           │           │                           │
│  S3: s3://provider-bucket │◄──────────│  Reads via pre-signed URLs│
└───────────────────────────┘  direct   └───────────────────────────┘
                                S3 read

  Auth: Metastore-to-metastore (automatic, no tokens)
  Data: Lives in provider S3, consumer reads directly
  Cost: S3 egress if cross-region
""")

elif solution in ["DELTA_SHARING_SNOWFLAKE", "DELTA_SHARING_POWER_BI", "DELTA_SHARING_OPEN_PROTOCOL"]:
    print(f"""
┌───────────────────────────┐           ┌───────────────────────────┐
│  DATABRICKS (Provider)    │           │  {platform:<25} │
│  ({inputs['provider_region']})         │           │  (Consumer)               │
│                           │           │                           │
│  demo_sales.gold_products │  Delta    │                           │
│  ├── revenue_dashboard    │  Sharing  │  Reads via .share profile │
│  ├── customer_segments    │──────────►│  (bearer token auth)      │
│  └── product_catalog      │  (Open    │                           │
│                           │  Protocol)│  Tables appear as:        │
│  SHARE: {consumer_slug}_share  │           │  Native {platform} tables   │
│  RECIPIENT: {consumer_slug}│           │                           │
│                           │           │                           │
│  S3: s3://provider-bucket │◄──────────│  Downloads Parquet via    │
└───────────────────────────┘  direct   │  pre-signed S3 URLs       │
                                HTTP    └───────────────────────────┘

  Auth: Bearer token in .share profile (from activation link)
  Data: Provider S3 → consumer via HTTPS (pre-signed URLs)
  Cost: S3 egress + consumer platform compute
""")

elif solution == "SHARED_EXTERNAL_LOCATION":
    print(f"""
┌───────────────────────────┐           ┌───────────────────────────┐
│  PROVIDER WORKSPACE       │           │  CONSUMER WORKSPACE       │
│                           │           │                           │
│  Pipeline writes to:      │           │  Reads from:              │
│  s3://shared-bucket/path/ │           │  s3://shared-bucket/path/ │
│  (IAM Role: write)        │           │  (IAM Role: read/write)   │
│                           │           │                           │
└─────────────┬─────────────┘           └─────────────┬─────────────┘
              │                                       │
              ▼                                       ▼
         ┌─────────────────────────────────────────────────┐
         │          S3: s3://shared-bucket/path/            │
         │          (Delta tables, shared storage)          │
         │          Both parties access same files          │
         └─────────────────────────────────────────────────┘

  Auth: Separate IAM roles with trust to each Unity Catalog
  Data: Single S3 location, both read (and optionally write)
  Cost: S3 storage (shared) + compute on each side
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 10: Summary & Input Recap

# COMMAND ----------

print("=" * 80)
print("  INPUT SUMMARY")
print("=" * 80)
print()
print("  ENVIRONMENT:")
print(f"    Same Metastore:     {inputs['same_metastore']}")
print(f"    Same Account:       {inputs['same_account']}")
print(f"    Same Region:        {inputs['same_region']}")
print(f"    Provider Region:    {inputs['provider_region']}")
print(f"    Consumer Region:    {inputs['consumer_region']}")
print(f"    Consumer Platform:  {inputs['consumer_platform']}")
print()
print("  IDENTITY & ACCESS:")
print(f"    Consumer Name:      {inputs['consumer_name']}")
print(f"    Identity Type:      {inputs['consumer_identity']}")
print(f"    Access Type:        {inputs['access_type']}")
print(f"    Groups Exist:       {inputs['groups_exist']}")
print(f"    External Consumer:  {inputs['consumer_external']}")
print()
print("  DATA:")
print(f"    Tables to Share:    {inputs['tables_to_share']}")
print(f"    Data Volume:        {inputs['data_volume']}")
print(f"    Contains PII:       {inputs['contains_pii']}")
print(f"    Classification:     {inputs['data_classification']}")
print(f"    Needs CDC:          {inputs['needs_cdc']}")
print()
print("  SLA & FRESHNESS:")
print(f"    Freshness:          {inputs['freshness_requirement']}")
print(f"    Duration:           {inputs['sharing_duration']}")
print()
print("  SECURITY:")
print(f"    Data Residency:     {inputs['data_residency']}")
print(f"    Column Security:    {inputs['needs_column_security']}")
print(f"    Row Security:       {inputs['needs_row_security']}")
print()
print("  CONSUMER NEEDS:")
print(f"    Transformation:     {inputs['consumer_needs_transform']}")
print()
print("=" * 80)
print(f"  RECOMMENDED:  {sol.get('name', result['primary_solution'])}")
print(f"  ALTERNATIVE:  {result['secondary_solution']}")
print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Architecture Advisor Complete!
# MAGIC 
# MAGIC **What this notebook does:**
# MAGIC 1. Collects your scenario inputs via widgets (dropdowns + text)
# MAGIC 2. Runs a decision engine analyzing all combinations
# MAGIC 3. Outputs: recommended solution, prerequisites, security, cost, implementation steps
# MAGIC 4. Generates ready-to-run SQL/code for both provider and consumer
# MAGIC 5. Draws an architecture diagram for your specific scenario
# MAGIC 
# MAGIC **To re-run with different inputs:**
# MAGIC - Change widget values at the top
# MAGIC - Re-run all cells (Cmd+Shift+Enter or Run All)
# MAGIC 
# MAGIC **Covers all combinations:**
# MAGIC - Same/different metastore
# MAGIC - Same/different account
# MAGIC - Same/different region
# MAGIC - Databricks / Snowflake / Power BI / Python / Spark / dbt
# MAGIC - Human / Service Principal / External app
# MAGIC - With/without PII, column/row security, data residency
# MAGIC - Read-only / Read-write
# MAGIC - One-time / Ongoing

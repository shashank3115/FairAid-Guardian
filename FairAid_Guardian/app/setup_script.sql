-- Setup Script for FairAid Guardian

CREATE APPLICATION ROLE IF NOT EXISTS app_public;
CREATE SCHEMA IF NOT EXISTS core;
GRANT USAGE ON SCHEMA core TO APPLICATION ROLE app_public;

-- 1. Create Synthetic Data (Demo Dataset)
-- We create this inside the app so it works out-of-the-box.
CREATE OR REPLACE TABLE core.demo_beneficiaries AS
WITH region_gen AS (
    SELECT 
        SEQ4() as id,
        UNIFORM(1, 4, RANDOM(12)) as region_id,
        UNIFORM(18, 90, RANDOM(12)) as age,
        ARRAY_CONSTRUCT('M', 'F', 'NB')[UNIFORM(0, 2, RANDOM(12))]::STRING as gender,
        UNIFORM(100, 5000, RANDOM(12)) as income_base
    FROM TABLE(GENERATOR(ROWCOUNT => 1000))
),
regions AS (
    SELECT 1 as rid, 'North' as region_name, 1.2 as bias_factor UNION ALL -- North gets more
    SELECT 2 as rid, 'South' as region_name, 0.8 as bias_factor UNION ALL -- South gets less (unfair)
    SELECT 3 as rid, 'East' as region_name, 1.0 as bias_factor UNION ALL
    SELECT 4 as rid, 'West' as region_name, 0.9 as bias_factor
)
SELECT 
    'BEN-' || LPAD(r.id, 5, '0') as beneficiary_id,
    rg.region_name as region,
    CASE 
        WHEN r.age < 30 THEN '18-29'
        WHEN r.age < 50 THEN '30-49'
        WHEN r.age < 70 THEN '50-69'
        ELSE '70+' 
    END as age_group,
    r.gender,
    CASE 
        WHEN r.income_base < 1000 THEN 'Low'
        WHEN r.income_base < 3000 THEN 'Medium'
        ELSE 'High'
    END as income_band,
    'Cash Assistance' as aid_type,
    ROUND(r.income_base * 0.1 * rg.bias_factor + UNIFORM(-50, 50, RANDOM(12)), 2) as amount_received,
    DATEADD(day, -UNIFORM(0, 365, RANDOM(12)), CURRENT_DATE()) as date_received
FROM region_gen r
JOIN regions rg ON r.region_id = rg.rid;

-- Add some duplicates for anomalies
INSERT INTO core.demo_beneficiaries
SELECT 
    beneficiary_id, region, age_group, gender, income_band, aid_type, amount_received, date_received
FROM core.demo_beneficiaries
SAMPLE(5);

GRANT SELECT ON TABLE core.demo_beneficiaries TO APPLICATION ROLE app_public;

-- 2. Analytics Views

-- Metric: Coverage & Distribution
CREATE OR REPLACE VIEW core.vw_coverage_stats AS
SELECT 
    region,
    COUNT(DISTINCT beneficiary_id) as total_beneficiaries,
    SUM(amount_received) as total_distributed,
    AVG(amount_received) as avg_amount,
    STDDEV(amount_received) as std_dev_amount
FROM core.demo_beneficiaries
GROUP BY region;

GRANT SELECT ON VIEW core.vw_coverage_stats TO APPLICATION ROLE app_public;

-- Metric: Fairness Analysis
CREATE OR REPLACE VIEW core.vw_fairness_analysis AS
WITH global_stats AS (
    SELECT AVG(amount_received) as global_avg FROM core.demo_beneficiaries
)
SELECT 
    c.region,
    c.avg_amount,
    g.global_avg,
    ROUND(((c.avg_amount - g.global_avg) / g.global_avg) * 100, 1) as percent_diff,
    CASE 
        WHEN ABS(percent_diff) > 20 THEN 'High Disparity'
        WHEN ABS(percent_diff) > 10 THEN 'Moderate Disparity'
        ELSE 'Fair'
    END as status,
    CASE
        WHEN percent_diff < -15 THEN 'Underfunded'
        WHEN percent_diff > 15 THEN 'Overfunded'
        ELSE 'Balanced'
    END as distribution_type
FROM core.vw_coverage_stats c, global_stats g;

GRANT SELECT ON VIEW core.vw_fairness_analysis TO APPLICATION ROLE app_public;

-- Metric: Anomalies (Duplicates & Outliers)
CREATE OR REPLACE VIEW core.vw_anomalies AS
SELECT 
    beneficiary_id,
    COUNT(*) as record_count,
    'Duplicate Record' as anomaly_type,
    'High' as risk_score
FROM core.demo_beneficiaries
GROUP BY beneficiary_id
HAVING count(*) > 1
UNION ALL
SELECT 
    beneficiary_id,
    1 as record_count,
    'Extreme Amount' as anomaly_type,
    'Medium' as risk_score
FROM core.demo_beneficiaries
WHERE amount_received > (SELECT AVG(amount_received) * 3 FROM core.demo_beneficiaries);

GRANT SELECT ON VIEW core.vw_anomalies TO APPLICATION ROLE app_public;

-- 3. AI Interface (Cortex Wrapper)
-- We allow Streamlit to call this.
CREATE OR REPLACE PROCEDURE core.get_ai_summary(region_name STRING)
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.8'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'generate_summary'
AS
$$
import snowflake.snowpark as snowpark
import json

def generate_summary(session, region_name):
    # 1. Fetch Stats
    df = session.table("core.vw_fairness_analysis").filter(snowpark.col("region") == region_name).collect()
    if not df:
        return "No data found for this region."
    
    row = df[0]
    stats = {
        "region": row['REGION'],
        "avg_aid": row['AVG_AMOUNT'],
        "global_avg": row['GLOBAL_AVG'],
        "difference_percent": row['PERCENT_DIFF'],
        "status": row['STATUS']
    }
    
    # 2. Construct Prompt using CORTEX
    # Note: In a real Native App, we might need to handle privileges carefully.
    # Assuming the Consumer Account supports Cortex.
    
    prompt = f"""
    You are a FairAid Guardian AI assistant. Analyze the following data for region {stats['region']}.
    
    Data:
    - Average Aid Received: ${stats['avg_aid']:.2f}
    - Global Average: ${stats['global_avg']:.2f}
    - Deviation: {stats['difference_percent']}%
    - Assessment: {stats['status']}
    
    Task:
    Write a 2-sentence executive summary explaining if this region is being treated fairly. 
    If there is a disparity, suggest one potential cause (e.g., outdated census data, remote inaccessibility).
    Keep it professional and empathetic.
    """
    
    # Call Cortex
    try:
        cmd = "SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3-70b', ?)"
        result = session.sql(cmd, params=[prompt]).collect()[0][0]
        return result
    except Exception as e:
        return f"AI Generation Unavailable: {str(e)}"
$$;

GRANT USAGE ON PROCEDURE core.get_ai_summary(STRING) TO APPLICATION ROLE app_public;

-- 4. Streamlit
CREATE OR REPLACE STREAMLIT core.fairaid_ui
FROM '/streamlit'
MAIN_FILE = 'fairaid_app.py';

GRANT USAGE ON STREAMLIT core.fairaid_ui TO APPLICATION ROLE app_public;

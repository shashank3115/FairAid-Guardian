import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import time

# --- MOCKING SNOWFLAKE SESSION ---
# Since we are running locally without a connection, we simulate the data.

st.set_page_config(layout="wide", page_title="FairAid Guardian [LOCAL DEMO]")

# Styling
st.markdown("""
    <style>
    .big-font { font-size: 20px !important; }
    .risk-high { background-color: #ffcccc; padding: 10px; border-radius: 5px; border-left: 5px solid red; }
    .risk-med { background-color: #fff4cc; padding: 10px; border-radius: 5px; border-left: 5px solid orange; }
    .stMetricValue { font-size: 28px; color: #2e7d32; }
    </style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([1, 4])
with col1:
    # Use a placeholder image or a public URL
    st.image("https://img.icons8.com/color/96/000000/balance.png", width=80) 
with col2:
    st.title("FairAid Guardian (Local Demo Mode)")
    st.markdown("**AI-Powered Fairness & Leakage Monitor for Public Aid Programs**")
    st.caption("ℹ️ Running in Local Mock Mode. Data is synthetic and generated in-memory.")

# --- MOCK DATA GENERATION ---
@st.cache_data
def load_mock_data():
    # Simulate the SQL logic from setup_script.sql
    np.random.seed(42)
    regions = ['North', 'South', 'East', 'West']
    bias = {'North': 1.2, 'South': 0.8, 'East': 1.0, 'West': 0.9}
    
    data = []
    for _ in range(1000):
        r = np.random.choice(regions)
        base_income = np.random.uniform(100, 5000)
        # Aid amount logic
        amount = base_income * 0.1 * bias[r] + np.random.uniform(-50, 50)
        amount = max(amount, 0)
        
        data.append({
            'BENEFICIARY_ID': f"BEN-{np.random.randint(10000,99999)}",
            'REGION': r,
            'AGE_GROUP': np.random.choice(['18-29', '30-49', '50-69', '70+']),
            'GENDER': np.random.choice(['M', 'F', 'NB']),
            'AMOUNT_RECEIVED': round(amount, 2),
            'DATE_RECEIVED': pd.Timestamp('now') - pd.Timedelta(days=np.random.randint(0,365))
        })
    
    df = pd.DataFrame(data)
    
    # Create Anomalies (Duplicates)
    dupes = df.sample(5).copy()
    dupes['AMOUNT_RECEIVED'] = dupes['AMOUNT_RECEIVED'] * 1.5 # Suspicious change
    df = pd.concat([df, dupes])
    
    return df

df_beneficiaries = load_mock_data()

# Calculate Logic (Simulating SQL Views)
# 1. Coverage
df_coverage = df_beneficiaries.groupby('REGION').agg(
    TOTAL_BENEFICIARIES=('BENEFICIARY_ID', 'nunique'),
    TOTAL_DISTRIBUTED=('AMOUNT_RECEIVED', 'sum'),
    AVG_AMOUNT=('AMOUNT_RECEIVED', 'mean')
).reset_index()

# 2. Fairness
global_avg = df_beneficiaries['AMOUNT_RECEIVED'].mean()
df_fairness = df_coverage.copy()
df_fairness['GLOBAL_AVG'] = global_avg
df_fairness['PERCENT_DIFF'] = ((df_fairness['AVG_AMOUNT'] - global_avg) / global_avg) * 100
df_fairness['STATUS'] = df_fairness['PERCENT_DIFF'].apply(lambda x: 'High Disparity' if abs(x) > 20 else ('Moderate Disparity' if abs(x) > 10 else 'Fair'))
df_fairness['DISTRIBUTION_TYPE'] = df_fairness['PERCENT_DIFF'].apply(lambda x: 'Underfunded' if x < -15 else ('Overfunded' if x > 15 else 'Balanced'))

# 3. Anomalies
dup_counts = df_beneficiaries.groupby('BENEFICIARY_ID').size()
dupes = dup_counts[dup_counts > 1].reset_index(name='record_count')
dupes['ANOMALY_TYPE'] = 'Duplicate Record'
dupes['RISK_SCORE'] = 'High'
df_anomalies = dupes.copy() # Simplification for demo


# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    st.selectbox("Data Source", ["core.demo_beneficiaries (Mocked)"])
    st.divider()
    
    st.subheader("Global Filter")
    selected_region = st.selectbox("Select Region for Deep Dive", ["All"] + df_coverage['REGION'].tolist())

# --- MAIN DASHBOARD ---

# KPIs
total_aid = df_coverage['TOTAL_DISTRIBUTED'].sum()
total_ben = df_coverage['TOTAL_BENEFICIARIES'].sum()
avg_aid = df_coverage['AVG_AMOUNT'].mean()
anomalies_count = len(df_anomalies)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Aid Disbursed", f"${total_aid:,.0f}")
kpi2.metric("Beneficiaries Reached", f"{total_ben:,}")
kpi3.metric("Avg Aid / Person", f"${avg_aid:,.2f}")
kpi4.metric("Anomalies Detected", f"{anomalies_count}", delta=f"-{anomalies_count}" if anomalies_count > 0 else "0", delta_color="inverse")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 Dashboard & Fairness", "🤖 AI Guardian Insights", "🚨 Anomalies & Data"])

with tab1:
    st.subheader("Regional Fairness Analysis")
    st.markdown("Comparing regional distribution against the global average.")
    
    # Bar Chart
    c = alt.Chart(df_fairness).mark_bar().encode(
        x='REGION',
        y='AVG_AMOUNT',
        color=alt.condition(
            alt.datum.PERCENT_DIFF < -10,
            alt.value("red"),
            alt.value("green")
        ),
        tooltip=['REGION', 'AVG_AMOUNT', 'PERCENT_DIFF', 'STATUS']
    ).properties(height=400)
    
    st.altair_chart(c, use_container_width=True)
    
    st.dataframe(df_fairness.style.map(lambda x: 'color: red' if 'High Disparity' in str(x) else 'color: black'), use_container_width=True)

with tab2:
    st.subheader("AI-Driven Policy Insights")
    st.info("Select a region in the Sidebar to generate a specific report.")
    
    if selected_region and selected_region != "All":
        if st.button(f"Generate Cortex Report for {selected_region}"):
            with st.spinner("Consulting AI Guardian (Simulated)..."):
                time.sleep(1.5) # Fake latency
                
                # Mock AI Retrieval Logic
                row = df_fairness[df_fairness['REGION'] == selected_region].iloc[0]
                diff = row['PERCENT_DIFF']
                
                if diff < -15:
                    summary = f"⚠️ **CRITICAL FINDING**: Region {selected_region} is severely underfunded ({diff:.1f}% below average). This suggests systemic exclusion or data gaps."
                    cause = "Potential Cause: Remote geography or lack of local registration offices."
                    action = "- 🚚 Deploy Mobile Registration Units immediately.\n- 💵 Allocate emergency supplementary budget."
                elif diff > 15:
                    summary = f"⚠️ **RISK FINDING**: Region {selected_region} is receiving significantly more aid ({diff:.1f}% above average). This may indicate duplication or lax criteria."
                    cause = "Potential Cause: Duplicate beneficiary lists or political bias."
                    action = "- 🔍 Initiate Audit of beneficiary list.\n- 🆔 Enforce biometric deduping."
                else:
                    summary = f"✅ **POSITIVE**: Region {selected_region} is within the fair range ({diff:.1f}% deviation). Distribution is equitable."
                    cause = "System appears to be working as intended."
                    action = "- Monitor for future changes."

                st.markdown(f"### 📢 Guardian Report: {selected_region}")
                st.write(summary)
                st.markdown(f"_{cause}_")
                st.markdown("#### Suggested Actions:")
                st.markdown(action)
    else:
        st.warning("Please select a specific Region in the sidebar to run the AI analysis.")

with tab3:
    col_risks, col_data = st.columns([1, 2])
    with col_risks:
        st.subheader("Active Risks")
        if not df_anomalies.empty:
            for index, row in df_anomalies.iterrows():
                st.error(f"High Risk: {row['BENEFICIARY_ID']} - Duplicate Record")
        else:
            st.success("No active risks detected.")
            
    with col_data:
        st.subheader("Raw Data Preview")
        st.dataframe(df_beneficiaries.head(20), use_container_width=True)

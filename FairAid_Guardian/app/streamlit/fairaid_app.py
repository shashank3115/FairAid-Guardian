import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session
import altair as alt

# Set page layout
st.set_page_config(layout="wide", page_title="FairAid Guardian")

# Setup Session
session = get_active_session()

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
    st.image("https://img.icons8.com/color/96/000000/balance.png", width=80) 
with col2:
    st.title("FairAid Guardian")
    st.markdown("**AI-Powered Fairness & Leakage Monitor for Public Aid Programs**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    data_source = st.selectbox("Data Source", ["core.demo_beneficiaries", "Custom (Not Configured)"])
    
    st.divider()
    
    st.subheader("Global Filter")
    # Fetch regions
    if data_source == "core.demo_beneficiaries":
        try:
            regions_df = session.sql("SELECT DISTINCT region FROM core.demo_beneficiaries").to_pandas()
            selected_region = st.selectbox("Select Region for Deep Dive", ["All"] + regions_df['REGION'].tolist())
        except Exception as e:
            st.error(f"Setup incomplete. Run Setup Script. {e}")
            selected_region = "All"
    else:
        st.info("Custom data source logic would go here.")

# Main Logic
try:
    # 1. Fetch High Level Metrics
    df_coverage = session.table("core.vw_coverage_stats").to_pandas()
    df_fairness = session.table("core.vw_fairness_analysis").to_pandas()
    df_anomalies = session.table("core.vw_anomalies").to_pandas()
    
    total_aid = df_coverage['TOTAL_DISTRIBUTED'].sum()
    total_ben = df_coverage['TOTAL_BENEFICIARIES'].sum()
    avg_aid = df_coverage['AVG_AMOUNT'].mean() # Average of averages effectively/roughly
    
    # 2. KPI Section
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Aid Disbursed", f"${total_aid:,.0f}")
    kpi2.metric("Beneficiaries Reached", f"{total_ben:,}")
    kpi3.metric("Avg Aid / Person", f"${avg_aid:,.2f}")
    
    # Calculate System Health
    anomalies_count = len(df_anomalies)
    kpi4.metric("Anomalies Detected", f"{anomalies_count}", delta=f"-{anomalies_count}" if anomalies_count > 0 else "0", delta_color="inverse")
    
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard & Fairness", "🤖 AI Guardian Insights", "🚨 Anomalies & Data"])
    
    with tab1:
        st.subheader("Regional Fairness Analysis")
        st.markdown("Comparing regional distribution against the global average.")
        
        # Combine fairness data for visualization
        chart_data = df_fairness[['REGION', 'AVG_AMOUNT', 'PERCENT_DIFF', 'STATUS', 'DISTRIBUTION_TYPE']]
        
        # Bar Chart
        c = alt.Chart(chart_data).mark_bar().encode(
            x='REGION',
            y='AVG_AMOUNT',
            color=alt.condition(
                alt.datum.PERCENT_DIFF < -10,
                alt.value("red"),  # The positive color
                alt.value("green") # The negative color
            ),
            tooltip=['REGION', 'AVG_AMOUNT', 'PERCENT_DIFF', 'STATUS']
        ).properties(height=400)
        
        st.altair_chart(c, use_container_width=True)
        
        st.subheader("Fairness Detail Grid")
        st.dataframe(chart_data.style.applymap(lambda x: 'color: red' if 'High Disparity' in str(x) else 'color: black'), use_container_width=True)

    with tab2:
        st.subheader("AI-Driven Policy Insights")
        st.info("Select a region in the Sidebar to generate a specific report.")
        
        if selected_region and selected_region != "All":
            if st.button(f"Generate Cortex Report for {selected_region}"):
                with st.spinner("Consulting AI Guardian..."):
                    try:
                        sql = f"CALL core.get_ai_summary('{selected_region}')"
                        summary = session.sql(sql).collect()[0][0]
                        
                        st.markdown(f"### 📢 Guardian Report: {selected_region}")
                        st.success(summary)
                        
                        # Add some fake "Actionable Steps" logic based on simple rules
                        st.markdown("#### Suggested Actions:")
                        row = df_fairness[df_fairness['REGION'] == selected_region].iloc[0]
                        if row['PERCENT_DIFF'] < -10:
                            st.write("- 🔍 **Audit Enrollment**: Enrollment rates are low. Deploy mobile registration teams.")
                            st.write("- 💰 **Review Allocation**: Immediate supplementary budget recommended.")
                        elif row['PERCENT_DIFF'] > 10:
                            st.write("- 📉 **Normalize**: Allocation exceeds standard implementation. Check for duplication.")
                        else:
                            st.write("- ✅ **Maintain**: Current levels are optimal.")
                            
                    except Exception as e:
                        st.error(f"Error generating AI summary: {e}")
        else:
            st.warning("Please select a specific Region in the sidebar to run the AI analysis.")
            
    with tab3:
        col_risks, col_data = st.columns([1, 2])
        
        with col_risks:
            st.subheader("Active Risks")
            if not df_anomalies.empty:
                for index, row in df_anomalies.iterrows():
                    risk_class = "risk-high" if row['RISK_SCORE'] == "High" else "risk-med"
                    st.markdown(f"""
                    <div class="{risk_class}">
                        <b>{row['RISK_SCORE']} RISK</b><br>
                        Beneficiary ID: {row['BENEFICIARY_ID']}<br>
                        Issue: {row['ANOMALY_TYPE']}
                    </div>
                    <br>
                    """, unsafe_allow_html=True)
            else:
                st.success("No active risks detected.")
                
        with col_data:
            st.subheader("Raw Data Preview")
            raw_data = session.table("core.demo_beneficiaries").limit(100).to_pandas()
            st.dataframe(raw_data, use_container_width=True)

except Exception as e:
    st.error(f"Application Error: {e}")
    st.warning("Ensure the Application Setup Script has run successfully.")


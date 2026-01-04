# FairAid Guardian ⚖️

**AI-Powered Fairness & Leakage Monitor for Public Aid Programs**  
*Built for the AI for Good Hackathon*

---

## 🚀 Overview
**FairAid Guardian** is a Snowflake Native App designed to help governments and NGOs monitor **fairness**, **coverage**, and **leakage** in public aid programs without manual auditing.

The app replaces repetitive, manual data checks with an install-in-minutes, reusable solution that runs entirely inside Snowflake, ensuring beneficiary data never leaves the secure environment.

---

## 🎯 The Problem
Public aid, health, and NGO programs frequently suffer from two opposing problems:
1.  **Leakage**: Funds are lost to duplicate enrollments or fraud (estimated 10-20% in some regions).
2.  **Exclusion**: Vulnerable populations are missed due to outdated census data or bias.

Agencies often lack the technical resources to audit this data continuously. They rely on static reports that arrive too late to fix the problem.

## 💡 The Solution
FairAid Guardian provides an instant "Fairness Engine" that:
*   **📊 Detects Regional Disparities**: Automatically calculates if a region is underfunded compared to the national average.
*   **🚨 Flags Leakage**: Identifies duplicate beneficiaries and suspicious aid amounts using SQL-based heuristics.
*   **🤖 Explains "Why" with AI**: Uses **Snowflake Cortex (Llama 3)** to generate privacy-safe, plain-language explanations for policy makers (e.g., *"Region South is underfunded likely due to remote inaccessibility"*).

---

## 🧠 AI for Good & Privacy Design
We prioritize **Data Privacy** and **Responsible AI**:
*   **Zero Data Movement**: The app installs *in* the consumer's account. No data is ever sent to the developer.
*   **Aggregated Intelligence**: The AI model (Cortex) is only ever fed **aggregated statistics** (e.g., "Region Avg: $100"), never individual PII. This prevents the AI from "memorizing" or leaking personal data.
*   **Explainability**: The AI suggests *potential* causes for human review, rather than making automated denial decisions.

---

## 🏗 Technical Architecture

This is a **Snowflake Native App** utilizing:
*   **Framework**: Snowflake Native App (Provider-Consumer Model)
*   **UI**: Streamlit in Snowflake (SiS)
*   **Compute**: Snowpark Python (Data Processing)
*   **Intelligence**: Snowflake Cortex (`llama3-70b`)
*   **Automation**: Streams & Tasks (optional for real-time updates)

---

## 📂 Repository Structure

```text
e:\AI_FOR_GOOD\FairAid_Guardian\
├── app/                        # NATIVE APP SOURCE CODE
│   ├── manifest.yml            # App Permissions & Config
│   ├── setup_script.sql        # Core Logic (Tables, Views, Stored Procs)
│   └── streamlit/              # Dashboard UI
│       ├── fairaid_app.py      # Streamlit Application
│       └── environment.yml     # Python Dependencies
└── README.md                   # Documentation
```

---

## 🛠 Installation & Usage

### Option A: Local Demo (No Snowflake Required)
We have included a specific version for local testing that mocks the Snowflake connection.
1. `pip install streamlit pandas altair`
2. `streamlit run app/streamlit/fairaid_app_local_demo.py`

### Option B: Deploy to Snowflake (Production)
1.  **Create an Application Package**:
    ```sql
    CREATE APPLICATION PACKAGE FairAid_Package;
    ```
2.  **Upload Files**:
    Upload the contents of the `app/` directory to a named stage (e.g., `@FairAid_Package.main.app_stage`).
3.  **Install Application**:
    ```sql
    CREATE APPLICATION FairAid_App
      FROM APPLICATION PACKAGE FairAid_Package
      USING '@FairAid_Package.main.app_stage';
    ```
4.  **Run**:
    Go to the **Apps** tab in Snowsight and click **FairAid Guardian**.
    *Note: The app allows you to generate a Synthetic Dataset on first launch.*

---

## 🎥 Demo
*To be added / [Link to YouTube Video]*

---

## 📜 License
MIT License - Open Source for the AI for Good Community.

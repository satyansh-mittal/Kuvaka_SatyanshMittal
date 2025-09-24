import os
import io
import requests
import streamlit as st

# Prefer Streamlit Secrets (Streamlit Cloud) then env, then localhost
BASE_URL = (
    (st.secrets.get("API_BASE_URL") if hasattr(st, "secrets") else None)
    or os.getenv("API_BASE_URL")
    or "http://localhost:8000"
)

st.set_page_config(page_title="Lead Scoring Tester", layout="centered")
st.title("Lead Intent Scoring - Tester")
st.caption(f"API: {BASE_URL}")

with st.expander("1) Set Offer", expanded=True):
    name = st.text_input("Offer Name", value="AI Outreach Automation")
    value_props = st.text_input("Value Props (comma-separated)", value="24/7 outreach,6x more meetings")
    ideal_use_cases = st.text_input("Ideal Use Cases (comma-separated)", value="B2B SaaS mid-market")

    if st.button("Save Offer"):
        vp = value_props if isinstance(value_props, list) else [s.strip() for s in value_props.split(',') if s.strip()]
        icp = [s.strip() for s in ideal_use_cases.split(',') if s.strip()]
        payload = {"name": name, "value_props": vp, "ideal_use_cases": icp}
        try:
            r = requests.post(f"{BASE_URL}/offer", json=payload, timeout=30)
            if r.ok:
                st.success("Offer saved.")
            else:
                st.error(f"Failed: {r.status_code} {r.text}")
        except Exception as e:
            st.error(f"Error: {e}")

with st.expander("2) Upload Leads CSV", expanded=True):
    f = st.file_uploader("Choose CSV", type=["csv"])
    if st.button("Upload CSV") and f is not None:
        try:
            files = {"file": (f.name, f.getvalue(), "text/csv")}
            r = requests.post(f"{BASE_URL}/leads/upload", files=files, timeout=60)
            if r.ok:
                st.success(r.json())
            else:
                st.error(f"Failed: {r.status_code} {r.text}")
        except Exception as e:
            st.error(f"Error: {e}")

with st.expander("3) Run Scoring", expanded=True):
    if st.button("Score Now"):
        try:
            r = requests.post(f"{BASE_URL}/score", timeout=120)
            if r.ok:
                data = r.json()
                st.success(f"Scored {len(data)} leads")
                st.dataframe(data)
            else:
                st.error(f"Failed: {r.status_code} {r.text}")
        except Exception as e:
            st.error(f"Error: {e}")

with st.expander("4) Results", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Refresh Results"):
            try:
                r = requests.get(f"{BASE_URL}/results", timeout=60)
                if r.ok:
                    st.dataframe(r.json())
                else:
                    st.error(f"Failed: {r.status_code} {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")
    with col2:
        if st.button("Download CSV"):
            try:
                r = requests.get(f"{BASE_URL}/results.csv", timeout=60)
                if r.ok:
                    st.download_button(label="Save results.csv", data=r.content, file_name="results.csv", mime="text/csv")
                else:
                    st.error(f"Failed: {r.status_code} {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")
st.caption("Tip: Set API_BASE_URL env var to point this UI to a deployed backend.")

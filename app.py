import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime

# ─────────────────────────────────────────────
# Config
API_URL = "https://cold-email-scraper.fly.dev"
API_KEY = os.getenv("API_KEY", "")
if not API_KEY:
    st.error("API_KEY not configured")
    st.stop()

TIERS = {
    "free": {"daily": 3, "monthly": 10},
    "starter": {"daily": 50, "monthly": 300},
    "pro": {"daily": 100, "monthly": 1000},
    "enterprise": {"daily": float('inf'), "monthly": float('inf')}
}

# ─────────────────────────────────────────────
# Session State Setup
if "usage" not in st.session_state:
    st.session_state.usage = {"daily": 0, "monthly": 0}
if "premium_tier" not in st.session_state:
    st.session_state.premium_tier = "free"
if "premium" not in st.session_state:
    st.session_state.premium = False

# ─────────────────────────────────────────────
# Fetch current premium tier
def fetch_status():
    try:
        r = requests.get(f"{API_URL}/status", headers={"X-API-Key": API_KEY}, timeout=10)
        if r.ok:
            tier = r.json().get("tier", "free")
            st.session_state.premium_tier = tier
            st.session_state.premium = tier != "free"
    except Exception:
        pass

fetch_status()

# ─────────────────────────────────────────────
# UI Setup
st.set_page_config(layout="wide", page_title="Cold Email Scraper Pro", page_icon="📬")
st.title("📬 Cold Email Scraper Pro")

# ─────────────────────────────────────────────
# Sidebar
with st.sidebar:
    st.subheader("Account Status")
    tier = st.session_state.premium_tier.title()
    limits = TIERS.get(st.session_state.premium_tier, TIERS['free'])
    st.metric("Plan", tier)

    if not st.session_state.premium:
        with st.expander("🔑 Activate Premium"):
            license_key = st.text_input("Enter License Key")
            if st.button("Activate Premium"):
                if not license_key:
                    st.warning("Please enter a license key")
                else:
                    try:
                        resp = requests.post(
                            f"{API_URL}/activate",
                            json={"key": license_key},
                            headers={"X-API-Key": API_KEY}
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("success"):
                                st.session_state.premium = True
                                st.session_state.premium_tier = data["tier"]
                                st.success(f"✅ Premium {data['tier'].title()} Activated!")
                                st.balloons()
                                fetch_status()
                            else:
                                st.error(f"❌ Activation failed: {data.get('error', 'Unknown error')}")
                        else:
                            st.error(f"❌ Activation failed ({resp.status_code}): {resp.text[:200]}")
                    except Exception as e:
                        st.error(f"🚨 Connection error: {str(e)}")
    else:
        if st.button("Deactivate Premium"):
            st.session_state.premium = False
            st.session_state.premium_tier = "free"
            st.success("✅ Premium Deactivated")

    st.divider()
    st.metric("🔍 Daily Searches", f"{st.session_state.usage['daily']}/{limits['daily']}")
    st.metric("🗓️ Monthly Searches", f"{st.session_state.usage['monthly']}/{limits['monthly']}")

# ─────────────────────────────────────────────
# Tabs
tab1, tab2 = st.tabs(["🔍 Search", "💎 Premium"])

# ────────────── SEARCH TAB ──────────────
with tab1:
    with st.form("search_form"):
        cols = st.columns(2)
        keyword = cols[0].text_input("Business Type", placeholder="e.g. dentist")
        location = cols[1].text_input("Location", placeholder="e.g. New York")

        tier = st.session_state.premium_tier
        max_map = {"free": 20, "starter": 50, "pro": 100, "enterprise": 200}
        max_results = max_map.get(tier, 20)

        count = st.slider("Number of Results", 5, max_results, min(max_results, 10))
        submitted = st.form_submit_button("🚀 Find Leads")

    if submitted:
        if not keyword or not location:
            st.warning("Please enter both keyword and location.")
        else:
            with st.spinner("Searching..."):
                try:
                    headers = {
                        "X-API-Key": API_KEY,
                        "Content-Type": "application/json"
                    }
                    resp = requests.post(
                        f"{API_URL}/scrape",
                        json={
                            "keyword": keyword,
                            "location": location,
                            "count": count
                        },
                        headers=headers,
                        timeout=60
                    )
                    try:
                        data = resp.json()
                    except Exception:
                        st.error("❌ Invalid JSON response from server.")
                        st.stop()

                    if resp.status_code != 200 or "error" in data:
                        error_msg = data.get("error", "Unknown error")
                        st.error(f"❌ API Error ({resp.status_code}): {error_msg}")
                        with st.expander("Debug Info"):
                            st.code(resp.text)
                        st.stop()

                    st.session_state.usage = data.get("usage", st.session_state.usage)
                    results = data.get("results", [])

                    if not results:
                        st.info("No leads found.")
                    else:
                        df = pd.DataFrame(results)
                        st.success(f"✅ Found {len(df)} leads!")
                        st.download_button(
                            "📥 Download CSV",
                            df.to_csv(index=False),
                            file_name=f"leads_{keyword}_{location}.csv"
                        )
                        st.dataframe(df)

                except Exception as e:
                    st.error(f"❌ Search failed: {str(e)}")

# ────────────── PREMIUM TAB ──────────────
with tab2:
    st.subheader("Upgrade Your Plan")
    cols = st.columns(3)
    with cols[0]:
        st.markdown("**Starter Plan**")
        st.write("- 50 searches/day")
        st.write("- Basic validation")
        st.write("- €9.99/month")
        st.link_button("Buy Now", "https://gumroad.com/l/starter")
    with cols[1]:
        st.markdown("**Pro Plan**")
        st.write("- 100 searches/day")
        st.write("- Full API access")
        st.write("- €24.99/month")
        st.link_button("Buy Now", "https://gumroad.com/l/pro")
    with cols[2]:
        st.markdown("**Enterprise**")
        st.write("- Unlimited searches")
        st.write("- Priority support")
        st.write("- Custom pricing")
        st.link_button("Contact Us", "mailto:support@example.com")

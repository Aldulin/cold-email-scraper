import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime

# Config
API_URL = "https://cold-email-scraper.fly.dev"
API_KEY = st.secrets.get("API_KEY", "")
TIERS = {
    "free": {"daily": 3, "monthly": 10},
    "starter": {"daily": 100, "monthly": 300},
    "pro": {"daily": 500, "monthly": 1500}
}

# Session state
if 'usage' not in st.session_state:
    st.session_state.update({
        'api_key': API_KEY,
        'premium': False,
        'usage': {'daily': 0, 'monthly': 0},
        'referral_code': st.query_params.get('ref', '')
    })

# UI
st.set_page_config(layout="wide", page_title="Cold Email Scraper Pro")
st.title("📬 Cold Email Scraper Pro")

# Sidebar
with st.sidebar:
    st.subheader("Account Status")
    tier = "Premium" if st.session_state.premium else "Free"
    st.metric("Plan", tier)
    
    if not st.session_state.premium:
        with st.sidebar.expander("🔑 Activate Premium"):
            license_key = st.text_input("Enter Gumroad License Key")
            if st.button("Activate Premium"):
                if not license_key:
                    st.warning("Please enter a license key")
                else:
                    try:
                        resp = requests.post(
                            f"{API_URL}/activate",
                            json={"key": license_key},
                            headers={"X-API-Key": st.session_state.api_key}
                        )

                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("success"):
                                st.session_state.premium = True
                                st.success(f"✅ Premium {data['tier'].title()} Activated!")
                                st.balloons()
                            else:
                                st.error(f"❌ Activation failed: {data.get('error', 'Unknown error')}")
                        else:
                            st.error(f"❌ Activation failed (HTTP {resp.status_code}): {resp.text[:200]}")
                    except Exception as e:
                        st.error(f"🚨 Connection error: {str(e)}")
    
    # Usage stats
    st.divider()
    st.metric("🔍 Daily Searches", 
             f"{st.session_state.usage['daily']}/{TIERS['free']['daily']}")
    st.metric("🗓️ Monthly", 
             f"{st.session_state.usage['monthly']}/{TIERS['free']['monthly']}")

# Main UI
tab1, tab2 = st.tabs(["🔍 Search", "💎 Premium"])

with tab1:
    with st.form("search_form"):
        cols = st.columns(2)
        keyword = cols[0].text_input("Business Type", placeholder="e.g. dentist")
        location = cols[1].text_input("Location", placeholder="e.g. New York")
        if st.session_state.get('premium_tier') == "pro":
            max_results = 100
        elif st.session_state.get('premium_tier') == "enterprise":
            max_results = 200
        else:
            max_results = 20  # Free or starter

        count = st.slider("Results", 5, max_results, min(max_results, 10))
        
        if st.form_submit_button("🚀 Find Leads"):
            if not keyword or not location:
                st.warning("Please enter both fields")
            else:
                with st.spinner("Searching..."):
                    API_KEYS = set()
                    try:
                        headers = {
                        "X-Referral-Code": st.session_state.referral_code or "",
                        "X-API-Key": st.session_state.api_key,
                        "Content-Type": "application/json"
                        }

                        api_url = API_URL.rstrip('/')
                        resp = requests.post(
                            f"{API_URL}/scrape",
                            json={"keyword": keyword, 
                                  "location": location, 
                                  "count": count
                                  },
                            headers=headers,
                            timeout=30
                        )
    
                        # Handle response status
                        try:
                            data = resp.json()
                        except ValueError:
                            st.error(f"Invalid response from server: {resp.text[:200]}")
                            st.stop()
        
                        if resp.status_code != 200:
                            st.error(f"API Error ({resp.status_code}): {data.get('error', 'Unknown error')}")
                            st.stop()

                        if "error" in data:
                            st.error(data["error"])
                            st.write("Status code:", resp.status_code)
                            st.write("Content-Type:", resp.headers.get("Content-Type", ""))
                            st.code(resp.text[:1000])  # Show raw response
                        else:
                            df = pd.DataFrame(data["results"])
                            if not df.empty:
                                st.download_button(
                                    "📥 Download CSV",
                                    df.to_csv(index=False),
                                    f"leads_{keyword}_{location}.csv"
                                )
                                st.dataframe(df)
                            else:
                                st.info("No leads found")
                    except Exception as e:
                        st.error(f"Search failed: {str(e)}")

with tab2:
    st.subheader("Upgrade Your Plan")
    cols = st.columns(3)
    with cols[0]:
        st.markdown("**Starter Plan**")
        st.write("- 50 searches/day")
        st.write("- Basic validation")
        st.write("- $9.99/month")
        st.link_button("Buy Now", "https://gumroad.com/l/starter")
    with cols[1]:
        st.markdown("**Pro Plan**")
        st.write("- 100 searches/day")
        st.write("- API access")
        st.write("- $24.99/month")
        st.link_button("Buy Now", "https://gumroad.com/l/pro")
    with cols[2]:
        st.markdown("**Enterprise**")
        st.write("- Unlimited searches")
        st.write("- Priority support")
        st.write("- Custom pricing")
        st.link_button("Contact Us", "mailto:support@example.com")

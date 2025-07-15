import streamlit as st
import pandas as pd
import requests
import time
import uuid
import os
from datetime import datetime

# Configuration
API_URL = os.getenv("API_URL", "https://cold-email-scraper.fly.dev/")
FREE_DAILY_SEARCHES = 3
REFERRAL_BONUS = 2
PROGRESS_STEPS = 5
MAX_RESULTS = 50 if os.getenv("TEST_MODE") == "true" else 20

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.update({
        'session_id': str(uuid.uuid4()),
        'referral_code': st.query_params.get('referral_code', None),
        'usage': {'daily': 0, 'monthly': 0, 'referrals': 0},
        'available_searches': FREE_DAILY_SEARCHES,
        'last_search': None
    })

# UI Setup
st.set_page_config(layout="wide", page_title="Cold Email Scraper Pro", page_icon="📬")
st.title("📬 Cold Email Scraper Pro")
st.caption("Advanced business lead generation with verified emails")

# Sidebar
with st.sidebar:
    st.subheader("Your Account")
    st.caption(f"**Session ID:** `{st.session_state.session_id[:8]}`")
    
    daily_used = st.session_state.usage['daily']
    daily_remaining = max(0, st.session_state.available_searches - daily_used)
    
    cols = st.columns(2)
    cols[0].metric("🔍 Daily", f"{daily_used}/{st.session_state.available_searches}")
    cols[1].metric("🗓️ Monthly", f"{st.session_state.usage['monthly']}/30")
    st.metric("👥 Referrals", st.session_state.usage['referrals'],
             f"+{st.session_state.usage['referrals'] * REFERRAL_BONUS} searches")
    
    # Referral
    st.divider()
    referral_link = f"{API_URL}?referral_code={st.session_state.session_id}"
    st.caption("Invite friends for bonus searches:")
    st.code(referral_link)
    st.button("📋 Copy Referral Link", key="copy_referral", help="Copy manually for now.")

# Search Form
with st.form("scrape_form"):
    col1, col2 = st.columns(2)
    keyword = col1.text_input("🔍 Business type", placeholder="e.g. dentist, gym")
    location = col2.text_input("📍 Location", placeholder="e.g. London, Berlin")
    count = st.slider("Results to fetch", 5, MAX_RESULTS, 10, 5)
    submit = st.form_submit_button("🚀 Scrape Leads")

# Submit action
if submit:
    if not keyword or not location:
        st.warning("Please enter both keyword and location")
        st.stop()

    with st.spinner("Processing your request..."):
        progress_bar = st.progress(0)
        result_container = st.empty()
        status_text = st.empty()

        headers = {
            "X-Referral-Code": st.session_state.referral_code or "",
            "Content-Type": "application/json"
        }
        payload = {
            "keyword": keyword,
            "location": location,
            "count": count
        }

        try:
            for i in range(PROGRESS_STEPS):
                status_text.info(f"🔍 Step {i+1}/{PROGRESS_STEPS}")
                progress_bar.progress((i + 1) * (100 // PROGRESS_STEPS))
                time.sleep(0.3)

            response = requests.post(f"{API_URL}scrape", json=payload, headers=headers, timeout=90)

            # Validate content type
            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("application/json"):
                result_container.error("🔥 Server returned non-JSON response.")
                with st.expander("Raw response"):
                    st.code(response.text[:1000])
                st.stop()

            try:
                data = response.json()
            except ValueError:
                result_container.error("🔥 Malformed JSON response.")
                with st.expander("Raw response"):
                    st.code(response.text[:1000])
                st.stop()

            # Handle specific errors
            if response.status_code == 429:
                st.error(f"❌ {data.get('error')}: limit {data.get('limit')}, used {data.get('used')}")
                st.stop()
            elif response.status_code != 200:
                st.error(f"❌ API Error: {data.get('error', 'Unknown error')}")
                st.stop()

            # Success
            st.session_state.usage = {
                'daily': data['usage']['daily'],
                'monthly': data['usage']['monthly'],
                'referrals': data['usage']['referrals']
            }

            results = data.get("results", [])
            df = pd.DataFrame(results)

            if df.empty:
                result_container.info("No leads found.")
            else:
                df = df[["name", "email", "phone", "website", "address", "rating"]]
                df = df[df["email"].notna() | df["phone"].notna()]

                result_container.success(f"✅ Found {len(df)} leads in {data['stats']['time']:.2f}s")

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"{keyword}_{location}_leads.csv",
                    mime="text/csv"
                )
                st.dataframe(df, use_container_width=True)

        except Exception as e:
            result_container.error(f"🔥 Unexpected error: {str(e)}")

        finally:
            progress_bar.progress(100)
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()

# Upsell section
st.divider()
st.subheader("🚀 Premium Features")
cols = st.columns(3)
cols[0].markdown("**Email Validation**\n- Verify email deliverability\n- Check domain reputation")
cols[1].markdown("**Advanced Filters**\n- Filter by company size\n- Tech stack detection")
cols[2].markdown("**API Access**\n- Direct API integration\n- Webhook support")

if st.button("✨ Upgrade Now", type="primary"):
    st.session_state.show_upgrade = True

if st.session_state.get('show_upgrade'):
    with st.expander("💎 Premium Plans", expanded=True):
        st.markdown("""
        | Plan        | Price  | Features |
        |-------------|--------|----------|
        | **Starter** | $9.99  | 100 searches/month, basic validation |
        | **Pro**     | $24.99 | 500 searches/month, API access |
        | **Enterprise** | Custom | Unlimited searches, dedicated support |
        """)

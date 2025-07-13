import streamlit as st
import pandas as pd
import requests
import time
import uuid
import json
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
    
    # Usage metrics
    daily_used = st.session_state.usage['daily']
    daily_remaining = max(0, st.session_state.available_searches - daily_used)
    
    cols = st.columns(2)
    cols[0].metric("🔍 Daily", f"{daily_used}/{st.session_state.available_searches}")
    cols[1].metric("🗓️ Monthly", f"{st.session_state.usage['monthly']}/30")
    st.metric("👥 Referrals", st.session_state.usage['referrals'],
             f"+{st.session_state.usage['referrals'] * REFERRAL_BONUS} searches")
    
    # Referral system
    st.divider()
    referral_link = f"{API_URL}?referral_code={st.session_state.session_id}"
    st.caption("Invite friends for bonus searches:")
    if st.button("📋 Copy Referral Link", key="copy_referral"):
        st.session_state.referral_code = st.session_state.session_id
        st.success("Copied to clipboard!")

# Main form
with st.form("scrape_form"):
    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input("🔍 Business type", placeholder="e.g. dentist, gym")
    with col2:
        location = st.text_input("📍 Location", placeholder="e.g. London, Berlin")
    
    count = st.slider("Results to fetch", 5, MAX_RESULTS, 10, 5)
    submit = st.form_submit_button("🚀 Scrape Leads")

if submit:
    if not keyword or not location:
        st.warning("Please enter both keyword and location")
    else:
        with st.spinner("Processing your request..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            result_container = st.empty()
            
            try:
                headers = {
                    "X-Referral-Code": st.session_state.referral_code or "",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "keyword": keyword, 
                    "location": location, 
                    "count": count
                }
                
                # Animated progress
                for i in range(PROGRESS_STEPS):
                    status_text.info(f"🔍 Step {i+1}/{PROGRESS_STEPS}: Processing...")
                    progress_bar.progress((i+1) * (100 // PROGRESS_STEPS))
                    time.sleep(0.3)
                
                # API call
                response = requests.post(
                    f"{API_URL}scrape",
                    json=payload,
                    headers=headers,
                    timeout=90
                )
                
                if response.status_code == 429:
                    error = response.json()
                    st.error(f"❌ {error.get('error')}: {error.get('used')}/{error.get('limit')} used")
                elif response.status_code != 200:
                    st.error(f"❌ Error: {response.text[:200]}")
                else:
                    data = response.json()
                    st.session_state.usage = {
                        'daily': data['usage']['daily'],
                        'monthly': data['usage']['monthly'],
                        'referrals': data['usage']['referrals']
                    }
                    st.session_state.last_search = datetime.now()
                    
                    if data.get('results'):
                        df = pd.DataFrame(data['results'])
                        df = df[["name", "email", "phone", "website", "address", "score"]]
                        df = df[df['email'].notna() | df['phone'].notna()]
                        
                        if not df.empty:
                            result_container.success(f"✅ Found {len(df)} leads in {data['stats']['time']:.1f}s")
                            
                            # Export options
                            csv = df.to_csv(index=False).encode("utf-8")
                            st.download_button(
                                "📥 Download CSV", 
                                csv,
                                file_name=f"{keyword}_{location}_leads.csv",
                                mime="text/csv"
                            )
                            
                            st.dataframe(df, use_container_width=True)
                        else:
                            result_container.info("No valid leads found")
                
            except Exception as e:
                result_container.error(f"🔥 Error: {str(e)}")
            finally:
                progress_bar.progress(100)
                time.sleep(0.5)
                progress_bar.empty()

# Upgrade section
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

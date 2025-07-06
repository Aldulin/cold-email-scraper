import streamlit as st
import pandas as pd
import requests
import time
import uuid

# Configuration
API_URL = "https://cold-email-scraper.fly.dev/"  # Update with your Fly.io URL
FREE_DAILY_SEARCHES = 3
REFERRAL_BONUS = 2

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.referral_code = None
    st.session_state.usage = {'daily': 0, 'monthly': 0, 'referrals': 0}
    st.session_state.available_searches = FREE_DAILY_SEARCHES

# --- UI Setup ---
st.set_page_config(layout="wide", page_title="Cold Email Scraper", page_icon="📬")
st.title("📬 Cold Email Scraper")
st.caption("Get business leads with verified emails - Free tier available!")

# Referral System
if 'referral_code' in st.query_params:
    st.session_state.referral_code = st.query_params['referral_code']
    st.success(f"🎉 Referral applied! You'll get extra searches")

# --- Sidebar ---
with st.sidebar:
    st.subheader("Your Account")
    st.caption(f"**Session ID:** `{st.session_state.session_id[:8]}`")
    
    # Show usage stats
    daily_remaining = max(0, st.session_state.available_searches - st.session_state.usage['daily'])
    st.metric("🔍 Daily Searches", 
              f"{st.session_state.usage['daily']}/{st.session_state.available_searches}",
              f"{daily_remaining} remaining")
    
    st.metric("🗓️ Monthly Searches", 
              f"{st.session_state.usage['monthly']}/{FREE_DAILY_SEARCHES*10}")
    
    st.metric("👥 Referrals", 
              st.session_state.usage['referrals'],
              f"+{st.session_state.usage['referrals'] * REFERRAL_BONUS} searches")
    
    # Referral link
    st.divider()
    referral_link = f"https://your-streamlit-app.com?referral_code={st.session_state.session_id}"
    st.caption("Invite friends and get bonus searches:")
    st.code(referral_link)
    if st.button("📋 Copy Referral Link"):
        st.session_state.referral_code = st.session_state.session_id
        st.success("Copied to clipboard!")

# --- Main Form ---
with st.form("scrape_form"):
    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input("🔍 Business type", placeholder="e.g. dentist, gym", key="kw")
    with col2:
        location = st.text_input("📍 Location", placeholder="e.g. London, Berlin", key="loc")
    
    count = st.slider("Results to fetch", 5, 30, 15, 5,
                      help="Free users limited to 15 results per search")
    submit = st.form_submit_button("🚀 Scrape Leads")

# --- Scrape Logic ---
if submit:
    if not keyword or not location:
        st.warning("Please enter both keyword and location")
    else:
        with st.spinner(f"Scraping {count} {keyword} in {location}..."):
            try:
                headers = {"X-Referral-Code": st.session_state.referral_code}
                payload = {
                    "keyword": keyword, 
                    "location": location, 
                    "count": min(count, 15)  # Free tier limit
                }
                
                response = requests.post(
                    f"{API_URL}/scrape",
                    json=payload,
                    headers=headers,
                    timeout=120
                )
                
                if response.status_code == 429:
                    error_data = response.json()
                    st.error(f"❌ {error_data['error']}: {error_data['used']}/{error_data['limit']} searches used")
                    st.info(f"**Pro Tip:** {error_data.get('referral_bonus', 'Invite friends for bonus searches')}")
                elif response.status_code != 200:
                    st.error(f"Error: {response.text}")
                else:
                    data = response.json()
                    st.session_state.usage = {
                        'daily': data['usage']['daily'],
                        'monthly': data['usage']['monthly'],
                        'referrals': data['usage']['referrals']
                    }
                    st.session_state.available_searches = FREE_DAILY_SEARCHES + (
                        st.session_state.usage['referrals'] * REFERRAL_BONUS
                    )
                    
                    df = pd.DataFrame(data['results'])
                    if not df.empty:
                        # Process results
                        df = df[df["email"].notna() | df["phone"].notna()]
                        df = df[["name", "email", "phone", "website", "address"]]
                        df.columns = [col.title() for col in df.columns]
                        
                        # Show results
                        email_count = df['Email'].notna().sum()
                        st.success(f"✅ Found {len(df)} leads ({email_count} with email)")
                        
                        # CSV Export
                        csv = df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            "📥 Download CSV", 
                            csv,
                            file_name=f"{keyword}_{location}_leads.csv",
                            mime="text/csv"
                        )
                        
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No valid leads found. Try different parameters")
            except Exception as e:
                st.error(f"Scraping failed: {str(e)}")

# --- Upgrade Section ---
st.divider()
st.subheader("🚀 Ready for Unlimited Access?")
c1, c2, c3 = st.columns(3)
with c1:
    st.write("**Free Tier**")
    st.write("3 searches/day")
    st.write("10 searches/month")
    st.write("Basic results")
with c2:
    st.write("**Pro Tier ($9.99)**")
    st.write("100 searches/month")
    st.write("Priority processing")
    st.write("Full exports")
with c3:
    st.write("**Unlimited ($24.99)**")
    st.write("Unlimited searches")
    st.write("API access")
    st.write("Dedicated support")

if st.button("✨ Upgrade Now", type="primary"):
    st.session_state.show_upgrade = True

if st.session_state.get('show_upgrade'):
    with st.expander("💎 Premium Options", expanded=True):
        st.write("**Special Launch Offer (First 100 customers):**")
        st.write("- Lifetime Pro Tier: $19.99 (reg. $99)")
        st.write("- 1 Year Unlimited: $29.99 (reg. $299)")
        st.write("👉 [Purchase on Gumroad](https://gumroad.com/your-product)")
        st.caption("After purchase, email receipt to support@yourapp.com for activation")

# --- Footer ---
st.markdown("---")
st.caption("""
    **Organic Growth Strategy:**  
    - Share your referral link for bonus searches  
    - Tweet about us to get 5 free bonus searches  
    - Tag us on LinkedIn for a feature shoutout  
    *No marketing budget needed!*
""")

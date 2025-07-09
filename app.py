import streamlit as st
import pandas as pd
import requests
import time
import uuid
import json

# Configuration
API_URL = "https://cold-email-scraper.fly.dev/"  # Update with your backend URL
FREE_DAILY_SEARCHES = 3
REFERRAL_BONUS = 2
PROGRESS_STEPS = 5  # Number of progress steps

TEST_MODE = False  # Set to True for testing 


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
    daily_used = st.session_state.usage['daily']
    daily_remaining = max(0, st.session_state.available_searches - daily_used)
    st.metric("🔍 Daily Searches", 
              f"{daily_used}/{st.session_state.available_searches}",
              f"{daily_remaining} remaining")
    
    st.metric("🗓️ Monthly Searches", 
              f"{st.session_state.usage['monthly']}/{FREE_DAILY_SEARCHES*10}")
    
    st.metric("👥 Referrals", 
              st.session_state.usage['referrals'],
              f"+{st.session_state.usage['referrals'] * REFERRAL_BONUS} searches")
    
    # Referral link
    st.divider()
    referral_link = f"https://your-app.com?referral_code={st.session_state.session_id}"
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
    
    count = st.slider("Results to fetch", 5, 30, 10, 5,
                      help="Free users limited to 10 results per search")
    submit = st.form_submit_button("🚀 Scrape Leads")

# --- Scrape Logic ---
if submit:
    if not keyword or not location:
        st.warning("Please enter both keyword and location")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        result_container = st.empty()
        
        try:
            headers = {
                "X-Referral-Code": st.session_state.referral_code or "",
                "Content-Type": "application/json"
            }

            if TEST_MODE:
                headers["X-Test-Mode"] = "true"

            payload = {
                "keyword": keyword, 
                "location": location, 
                "count": min(count, 10)  # Free tier limit
            }
            
            # Show progress
            for i in range(PROGRESS_STEPS):
                status_text.info(f"🔍 Step {i+1}/{PROGRESS_STEPS}: Processing...")
                progress_bar.progress((i+1) * (100 // PROGRESS_STEPS))
                time.sleep(0.3)
            
            # Make API request
            full_url = f"{API_URL}scrape"
            response = requests.post(
                full_url,
                json=payload,
                headers=headers,
                timeout=90  # Extended timeout
            )
            # DEBUGGING: Print URL and status code
            print(f"Request URL: {full_url}")
            print(f"Status Code: {response.status_code}")
            
            # Handle response content
            content_type = response.headers.get('Content-Type', '')
            is_json = 'application/json' in content_type
            if not is_json:
                result_container.error(f"🔥 Server returned non-JSON response (Status: {response.status_code})")
                with st.expander("Response Details"):
                    st.write(f"URL: {full_url}")
                    st.write(f"Status Code: {response.status_code}")
                    st.write(f"Content Type: {content_type}")
                    st.code(response.text[:1000])
                progress_bar.empty()
                status_text.empty()
                st.stop()
            
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                result_container.error("🔥 Failed to parse JSON response")
                with st.expander("Show response content"):
                    st.code(response.text[:1000])
                progress_bar.empty()
                status_text.empty()
                st.stop()
            
            
            if response.status_code == 429:
                error_data = response_data
                st.error(f"❌ {error_data.get('error', 'Limit reached')}: {error_data.get('used', '?')}/{error_data.get('limit', '?')} searches used")
                if "referral_bonus" in error_data:
                    st.info(f"**Pro Tip:** {error_data['referral_bonus']}")
            elif response.status_code != 200:
                error_data = response_data
                st.error(f"❌ Backend Error: {error_data.get('error', 'Unknown error')}")
                if "details" in error_data:
                    with st.expander("Technical Details"):
                        st.code(error_data.get("details", "No details"))
            else:
                data = response_data
                st.session_state.usage = {
                    'daily': data['usage']['daily'],
                    'monthly': data['usage']['monthly'],
                    'referrals': data['usage']['referrals']
                }
                st.session_state.available_searches = FREE_DAILY_SEARCHES + (
                    st.session_state.usage['referrals'] * REFERRAL_BONUS
                )
                
                # Process results
                if data.get('results'):
                    df = pd.DataFrame(data['results'])
                    # Filter and rename columns
                    df = df[["name", "email", "phone", "website", "address"]]
                    df.columns = [col.title() for col in df.columns]
                    
                    # Filter out rows without contact info
                    df = df[df['Email'].notna() | df['Phone'].notna()]
                    
                    if not df.empty:
                        # Show results
                        email_count = df['Email'].notna().sum()
                        result_container.success(f"✅ Found {len(df)} leads ({email_count} with email) in {data['stats']['time']:.1f}s")
                        
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
                        result_container.info("No valid leads found. Try different parameters")
                else:
                    result_container.info("No results found. Try different search terms")
                    
        except requests.exceptions.Timeout:
            result_container.error("⌛ Request timed out. Try fewer results.")
        except Exception as e:
            result_container.error(f"🔥 Unexpected error: {str(e)}")
        finally:
            time.sleep(0.5)
            progress_bar.progress(100)
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()

# --- Upgrade Section ---
st.divider()
st.subheader("🚀 Ready for Unlimited Access?")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Free Tier**")
    st.markdown("- 3 searches/day\n- 10 searches/month\n- Basic results")
with c2:
    st.markdown("**Pro Tier ($9.99/month)**")
    st.markdown("- 100 searches/month\n- Priority processing\n- Full exports")
with c3:
    st.markdown("**Unlimited ($24.99/month)**")
    st.markdown("- Unlimited searches\n- API access\n- Dedicated support")

if st.button("✨ Upgrade Now", type="primary", key="upgrade_button"):
    st.session_state.show_upgrade = True

if st.session_state.get('show_upgrade'):
    with st.expander("💎 Premium Options", expanded=True):
        st.markdown("**Special Launch Offer (First 100 customers):**")
        st.markdown("- Lifetime Pro Tier: $19.99 (reg. $99)")
        st.markdown("- 1 Year Unlimited: $29.99 (reg. $299)")
        st.markdown("👉 [Purchase on Gumroad](https://gumroad.com/your-product)")
        st.caption("After purchase, email receipt to support@yourapp.com for activation")

# --- Footer ---
st.markdown("---")
st.markdown("""
    **Organic Growth Strategy:**  
    - Share your referral link for bonus searches  
    - Tweet about us to get 5 free bonus searches  
    - Tag us on LinkedIn for a feature shoutout  
    *No marketing budget needed!*
""")

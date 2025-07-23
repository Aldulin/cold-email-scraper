import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timezone
import time

# ─────────────────────────────────────────────
# Config
API_URL = "https://cold-email-scraper.fly.dev"
API_KEY = os.getenv("API_KEY", "MjqbNu3Nbwu8KnHzbEbLIE7T23KETZOMbhID-dQ3Vk4")  # Add fallback
if not API_KEY:
    st.error("API_KEY not configured")
    st.info("Using fallback API key for testing")
    API_KEY = "MjqbNu3Nbwu8KnHzbEbLIE7T23KETZOMbhID-dQ3Vk4"

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
if "api_key" not in st.session_state:
    st.session_state.api_key = API_KEY  # Use default API key for free tier
if "last_results" not in st.session_state:
    st.session_state.last_results = []
if "search_history" not in st.session_state:
    st.session_state.search_history = []

# ─────────────────────────────────────────────
# Fetch current premium tier
def fetch_status():
    try:
        with st.spinner("Checking account status..."):
            headers = {
                "X-API-Key": st.session_state.api_key
            }
            
            r = requests.get(f"{API_URL}/status", headers=headers, timeout=10)
            if r.ok:
                data = r.json()
                tier = data.get("tier", "free")
                st.session_state.premium_tier = tier
                st.session_state.premium = tier != "free"
                st.session_state.usage = data.get("usage", {"daily": 0, "monthly": 0})
                st.session_state.reset = data.get("reset", {})
                return True
            elif r.status_code == 401:
                # Invalid API key - use defaults
                st.session_state.premium_tier = "free"
                st.session_state.premium = False
                st.session_state.usage = {"daily": 0, "monthly": 0}
                st.session_state.reset = {}
                st.warning("⚠️ API key not recognized - using free tier")
                return False
            elif r.status_code == 404:
                # Status endpoint doesn't exist - set defaults
                st.session_state.premium_tier = "free"
                st.session_state.premium = False
                st.session_state.usage = {"daily": 0, "monthly": 0}
                st.session_state.reset = {}
                st.warning("⚠️ Status endpoint not available - using defaults")
                return False
            else:
                error_detail = ""
                try:
                    error_data = r.json()
                    error_detail = error_data.get("error", "Unknown error")
                except:
                    error_detail = r.text[:200]
                
                st.error(f"Failed to fetch status: HTTP {r.status_code} - {error_detail}")
                return False
    except requests.exceptions.Timeout:
        st.error("⏰ Request timeout - server may be slow")
        return False
    except requests.exceptions.ConnectionError:
        st.error("🔌 Connection failed - check your internet or API URL")
        return False
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return False

fetch_status()

# ─────────────────────────────────────────────
# UI Setup
st.set_page_config(layout="wide", page_title="Cold Email Scraper Pro", page_icon="📬")
st.title("📬 Cold Email Scraper Pro")
tier = st.session_state.premium_tier      

reset = st.session_state.get("reset", {})
now = datetime.now(timezone.utc)

def time_until(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        delta = dt - now
        if delta.total_seconds() <= 0:
            return "now"
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        return f"in {hours}h {minutes}m"
    except:
        return "unknown"

# ─────────────────────────────────────────────
# Sidebar
with st.sidebar:
    st.subheader("📊 Account Status")
    
    # Status indicator
    if st.session_state.premium:
        st.success(f"✅ {tier.title()} Plan Active")
    else:
        st.info("💫 Free Plan")
    
    # License Key Activation - Always visible at the top
    st.subheader("🎫 Activate Premium")
    if not st.session_state.premium:
        st.info("Enter your license key to unlock premium features")
    else:
        st.success("Premium subscription active!")
    
    license_key = st.text_input(
        "License Key", 
        placeholder="Enter your purchase license key",
        help="Use test keys: TEST_STARTER, TEST_PRO, TEST_ENTERPRISE"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Activate", type="primary", disabled=not license_key):
            if license_key:
                try:
                    resp = requests.post(
                        f"{API_URL}/activate",
                        json={"key": license_key},
                        headers={
                            "X-API-Key": license_key
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("success"):
                            # Save the premium API key
                            st.session_state.api_key = data["api_key"]
                            st.success(f"✅ Premium {data['tier'].title()} Activated!")
                            st.info(f"🔑 **Your Premium API Key:** `{data['api_key']}`")
                            st.warning("⚠️ **IMPORTANT**: Save this API key to use on other devices!")
                            st.session_state.premium = True
                            st.session_state.premium_tier = data["tier"]
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ Activation failed: {data.get('error', 'Invalid license key')}")
                    else:
                        st.error("❌ Activation failed")
                except Exception as e:
                    st.error(f"🚨 Connection error: {str(e)}")
    
    with col2:
        if st.session_state.premium:
            if st.button("🚪 End Session", type="secondary", help="End your premium session"):
                try:
                    resp = requests.post(
                        f"{API_URL}/logout",
                        headers={
                            "X-API-Key": st.session_state.api_key  # Use current API key, not the fallback
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("success"):
                            # Reset to free tier with fallback API key
                            st.session_state.api_key = API_KEY  # Reset to free tier API key
                            st.session_state.premium = False
                            st.session_state.premium_tier = "free"
                            st.session_state.usage = {"daily": 0, "monthly": 0}
                            st.session_state.reset = {}
                            st.success("✅ Premium session ended")
                            st.info("💡 Your subscription is still active - login anytime with your premium API key")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ Session end failed: {data.get('error', 'Unknown error')}")
                    else:
                        st.error("❌ Failed to end session")
                except Exception as e:
                    st.error(f"🚨 Connection error: {str(e)}")
                    # Force reset even if server call fails
                    st.session_state.api_key = API_KEY
                    st.session_state.premium = False
                    st.session_state.premium_tier = "free"
                    st.session_state.usage = {"daily": 0, "monthly": 0}
                    st.session_state.reset = {}
                    st.warning("Session ended locally due to connection error")
                    time.sleep(1)
                    st.rerun()
        else:
            # Premium login for existing users
            if st.button("🔑 Have API Key?", help="Login with existing premium API key"):
                st.session_state.show_login = True
    
    # Collapsible login section for existing premium users
    if st.session_state.get("show_login", False) and not st.session_state.premium:
        with st.expander("🔐 Premium Login", expanded=True):
            st.info("Already have a premium API key? Enter it here:")
            premium_key = st.text_input("Premium API Key", type="password")
            
            col_login, col_cancel = st.columns(2)
            with col_login:
                if st.button("Login", type="primary"):
                    if premium_key:
                        try:
                            resp = requests.post(
                                f"{API_URL}/login",
                                json={"premium_key": premium_key},
                                headers={
                                    "X-API-Key": premium_key
                                }
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                if data.get("success"):
                                    # Save the premium API key
                                    st.session_state.api_key = premium_key
                                    st.session_state.premium = True
                                    st.session_state.premium_tier = data["tier"]
                                    st.session_state.show_login = False
                                    st.success(f"✅ Logged in as {data['tier'].title()}!")
                                    st.balloons()
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error("❌ Invalid premium API key")
                            else:
                                st.error("❌ Login failed")
                        except Exception as e:
                            st.error(f"🚨 Connection error: {str(e)}")
                    else:
                        st.warning("Please enter your premium API key")
            
            with col_cancel:
                if st.button("Cancel"):
                    st.session_state.show_login = False
                    st.rerun()
    
    st.divider()
    
    # Usage metrics
    usage_daily = st.session_state.usage.get('daily', 0)
    usage_monthly = st.session_state.usage.get('monthly', 0)
    limits = TIERS.get(tier, TIERS['free'])
    
    # Daily usage
    daily_percentage = min(usage_daily / limits['daily'], 1.0) if limits['daily'] != float('inf') else 0
    st.metric(
        "🔍 Daily Searches", 
        f"{usage_daily}/{limits['daily'] if limits['daily'] != float('inf') else '∞'}"
    )
    if limits['daily'] != float('inf'):
        st.progress(daily_percentage)
        if daily_percentage >= 0.8:
            st.warning(f"⚠️ {int((1-daily_percentage)*limits['daily'])} searches left today")
    
    # Monthly usage
    monthly_percentage = min(usage_monthly / limits['monthly'], 1.0) if limits['monthly'] != float('inf') else 0
    st.metric(
        "🗓️ Monthly Searches", 
        f"{usage_monthly}/{limits['monthly'] if limits['monthly'] != float('inf') else '∞'}"
    )
    if limits['monthly'] != float('inf'):
        st.progress(monthly_percentage)
        if monthly_percentage >= 0.8:
            st.warning(f"⚠️ {int((1-monthly_percentage)*limits['monthly'])} searches left this month")
    
    # Reset times
    if st.session_state.get("reset"):
        reset = st.session_state.reset
        if "daily" in reset:
            st.caption(f"🔁 Daily limit resets {time_until(reset['daily'])}")
        if "monthly" in reset:
            st.caption(f"📅 Monthly limit resets {time_until(reset['monthly'])}")
    
    st.divider()
    
    # Plan information
    st.subheader("💎 Upgrade Plans")
    if not st.session_state.premium:
        st.info("Unlock more searches with premium!")
        
        # Compact plan display
        with st.expander("View Plans"):
            st.markdown("""
            **🥉 Starter** - €9.99/month
            - 50 searches/day
            - Basic features
            
            **🥈 Pro** - €24.99/month  
            - 100 searches/day
            - Advanced features
            
            **🥇 Enterprise** - Custom
            - Unlimited searches
            - Priority support
            """)
            
            st.link_button("🛒 Purchase License", "https://gumroad.com/l/cold-email-scraper")
    else:
        st.success(f"You have {tier.title()} plan")
        
        # Show session info
        if st.session_state.get("reset", {}).get("monthly"):
            reset_date = st.session_state.reset["monthly"]
            st.caption(f"📅 Subscription resets {time_until(reset_date)}")
    
    # Utility section at bottom
    st.divider()
    if st.button("🧹 Clear Results", help="Clear previous search results"):
        st.session_state.last_results = []
        st.session_state.search_history = []
        st.success("Previous results cleared")
        time.sleep(1)
        st.rerun()
    
    # Add debug reset button
    if st.button("🔄 Reset Session", help="Force reset to free tier"):
        st.session_state.api_key = API_KEY
        st.session_state.premium = False
        st.session_state.premium_tier = "free"
        st.session_state.usage = {"daily": 0, "monthly": 0}
        st.session_state.reset = {}
        st.session_state.last_results = []
        st.session_state.search_history = []
        if "show_login" in st.session_state:
            del st.session_state.show_login
        st.success("Session reset to free tier")
        time.sleep(1)
        st.rerun()

# ─────────────────────────────────────────────
# Tabs
tab1, tab2 = st.tabs(["🔍 Search", "💎 Premium"])

# ────────────── SEARCH TAB ──────────────
with tab1:
    # In the search form, add quick selections
    with st.form("search_form"):
        # Previous searches dropdown
        if st.session_state.search_history:
            recent_searches = [f"{h['keyword']} in {h['location']}" for h in st.session_state.search_history[-5:]]
            selected_recent = st.selectbox("Recent Searches", [""] + recent_searches)
            if selected_recent:
                recent_data = next(h for h in st.session_state.search_history if f"{h['keyword']} in {h['location']}" == selected_recent)
                keyword = st.text_input("Business Type", value=recent_data['keyword'])
                location = st.text_input("Location", value=recent_data['location'])
            else:
                keyword = st.text_input("Business Type", placeholder="e.g. dentist")
                location = st.text_input("Location", placeholder="e.g. New York")
        else:
            keyword = st.text_input("Business Type", placeholder="e.g. dentist")
            location = st.text_input("Location", placeholder="e.g. New York")

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
                        "X-API-Key": st.session_state.api_key
                    }
                    
                    resp = requests.post(
                        f"{API_URL}/scrape",
                        json={"keyword": keyword, "location": location, "count": count},
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
                    st.session_state.last_results = results
                    
                    # Add to search history here (after results is defined)
                    if results:
                        search_entry = {
                            "keyword": keyword,
                            "location": location,
                            "timestamp": datetime.now().isoformat(),
                            "count": len(results)
                        }
                        st.session_state.search_history.append(search_entry)
                        # Keep only last 10 searches
                        st.session_state.search_history = st.session_state.search_history[-10:]
                    
                    if not results:
                        st.info("🔍 No leads found for this search.")
                    else:
                        df = pd.DataFrame(results)
                        
                        # Better metrics display
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Leads", len(df))
                        with col2:
                            emails_found = len(df[df['email'].notna()]) if 'email' in df.columns else 0
                            st.metric("With Email", emails_found)
                        with col3:
                            phones_found = len(df[df['phone'].notna()]) if 'phone' in df.columns else 0
                            st.metric("With Phone", phones_found)
                        
                        # Download options
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                "📥 Download All (CSV)",
                                df.to_csv(index=False),
                                file_name=f"leads_{keyword}_{location}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                mime="text/csv"
                            )
                        with col2:
                            # Download only leads with emails
                            if emails_found > 0:
                                email_df = df[df['email'].notna()]
                                st.download_button(
                                    "📧 Download Email Leads Only",
                                    email_df.to_csv(index=False),
                                    file_name=f"email_leads_{keyword}_{location}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                    mime="text/csv"
                                )
                        
                        # Enhanced data display
                        st.dataframe(
                            df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "email": st.column_config.TextColumn("Email", help="Contact email"),
                                "phone": st.column_config.TextColumn("Phone", help="Contact phone"),
                                "website": st.column_config.LinkColumn("Website"),
                            }
                        )

                except Exception as e:
                    st.error(f"❌ Search failed: {str(e)}")

# ────────────── PREMIUM TAB ──────────────
with tab2:
    st.subheader("💎 Premium Plans & Features")
    
    # Get current usage and limits
    usage_daily = st.session_state.usage.get('daily', 0)
    usage_monthly = st.session_state.usage.get('monthly', 0)
    limits = TIERS.get(tier, TIERS['free'])
    
    # Current status
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.premium:
            st.success(f"✅ You have {tier.title()} Plan")
            st.metric("Current Tier", tier.title())
        else:
            st.info("📋 You are on the Free Plan")
            st.metric("Current Searches", f"{usage_daily}/3 daily")
    
    with col2:
        if st.session_state.premium:
            daily_limit = limits['daily'] if limits['daily'] != float('inf') else "Unlimited"
            st.metric("Daily Limit", daily_limit)
        else:
            st.warning("⚡ Upgrade to unlock more searches!")
    
    st.divider()
    
    # Plan comparison
    st.subheader("📊 Plan Comparison")
    
    plan_data = {
        "Feature": [
            "Daily Searches",
            "Monthly Searches", 
            "Email Extraction",
            "Export Options",
            "Search History",
            "Priority Support",
            "Price"
        ],
        "Free": [
            "3", "10", "✅", "❌" , "❌", "❌", "€0"
        ],
        "Starter": [
            "50", "300", "✅", "CSV", "✅", "❌", "€9.99/month"
        ],
        "Pro": [
            "100", "1000", "✅", "CSV", "✅", "✅", "€24.99/month"
        ],
        "Enterprise": [
            "Unlimited", "Unlimited", "✅", "All formats", "✅", "✅", "Contact us"
        ]
    }
    
    comparison_df = pd.DataFrame(plan_data)
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Purchase options
    st.subheader("🛒 Get Premium")
    
    cols = st.columns(3)
    with cols[0]:
        with st.container():
            st.markdown("### 🥉 Starter")
            st.markdown("**€9.99/month**")
            st.markdown("Perfect for small businesses")
            st.markdown("- 50 searches/day")
            st.markdown("- 300 searches/month")
            st.markdown("- Email extraction")
            st.link_button("Buy Starter", "https://gumroad.com/l/starter", use_container_width=True)
    
    with cols[1]:
        with st.container():
            st.markdown("### 🥈 Pro")
            st.markdown("**€24.99/month**")
            st.markdown("Most popular choice")
            st.markdown("- 100 searches/day")
            st.markdown("- 1000 searches/month") 
            st.markdown("- Priority support")
            st.link_button("Buy Pro", "https://gumroad.com/l/pro", use_container_width=True)
    
    with cols[2]:
        with st.container():
            st.markdown("### 🥇 Enterprise")
            st.markdown("**Custom pricing**")
            st.markdown("For large organizations")
            st.markdown("- Unlimited searches")
            st.markdown("- Custom integrations")
            st.markdown("- Dedicated support")
            st.link_button("Contact Sales", "mailto:sales@example.com", use_container_width=True)
    
    st.divider()
    
    # How to activate
    st.subheader("🎫 How to Activate")
    
    st.markdown("""
    1. **Purchase** a license key from one of the links above
    2. **Copy** the license key from your purchase email
    3. **Paste** it in the sidebar activation box
    4. **Click** Activate to unlock premium features
    
    Your premium API key will be generated and can be used on any device!
    """)
    
    # FAQ
    with st.expander("❓ Frequently Asked Questions"):
        st.markdown("""
        **Q: How do I get my license key?**
        A: After purchase, you'll receive a license key via email. Use this to activate premium.
        
        **Q: Can I use premium on multiple devices?**
        A: Yes! Save your premium API key and use it to login on any device.
        
        **Q: What happens if I end my session?**
        A: Your subscription remains active. You can login again anytime with your premium API key.
        
        **Q: How do I cancel my subscription?**
        A: Contact support at support@example.com for cancellation requests.
        
        **Q: Do searches reset daily?**
        A: Yes, daily limits reset at midnight UTC. Monthly limits reset on the same day each month.
        """)

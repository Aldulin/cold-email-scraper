import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timezone
import time

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

if "last_results" not in st.session_state:
    st.session_state.last_results = []

# Add to session state initialization
if "search_history" not in st.session_state:
    st.session_state.search_history = []

# ─────────────────────────────────────────────
# Fetch current premium tier
def fetch_status():
    try:
        with st.spinner("Checking account status..."):
            r = requests.get(f"{API_URL}/status", headers={"X-API-Key": API_KEY}, timeout=10)
            if r.ok:
                data = r.json()
                tier = data.get("tier", "free")
                st.session_state.premium_tier = tier
                st.session_state.premium = tier != "free"
                st.session_state.usage = data.get("usage", {"daily": 0, "monthly": 0})
                st.session_state.reset = data.get("reset", {})
                return True
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

# Add debug button to frontend
if st.sidebar.button("🔍 Debug Info"):
    try:
        debug_resp = requests.get(f"{API_URL}/debug", headers={"X-API-Key": API_KEY})
        if debug_resp.ok:
            debug_data = debug_resp.json()
            st.sidebar.json(debug_data)
        else:
            st.sidebar.error(f"Debug failed: {debug_resp.status_code}")
    except Exception as e:
        st.sidebar.error(f"Debug error: {e}")

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
                    st.session_state.last_results = results
                    
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

                # After successful search, add to history
                if submitted and results:
                    search_entry = {
                        "keyword": keyword,
                        "location": location,
                        "timestamp": datetime.now().isoformat(),
                        "count": len(results)
                    }
                    st.session_state.search_history.append(search_entry)
                    # Keep only last 10 searches
                    st.session_state.search_history = st.session_state.search_history[-10:]

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

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_tier_limits(tier):
    return TIERS.get(tier, TIERS['free'])

# Add auto-refresh functionality
def auto_refresh_status():
    if "last_status_check" not in st.session_state:
        st.session_state.last_status_check = 0
    
    # Refresh every 5 minutes
    if time.time() - st.session_state.last_status_check > 300:
        fetch_status()
        st.session_state.last_status_check = time.time()

auto_refresh_status()

# Better API configuration check
def validate_config():
    issues = []
    if not API_KEY:
        issues.append("❌ API_KEY environment variable not set")
    if not API_URL:
        issues.append("❌ API_URL not configured")
    
    if issues:
        st.error("Configuration Issues:")
        for issue in issues:
            st.write(issue)
        st.info("Please check your environment variables and restart the app.")
        st.stop()

validate_config()

# Enhanced sidebar with session management
with st.sidebar:
    st.subheader("📊 Account Status")
    
    # Status indicator
    if st.session_state.premium:
        st.success(f"✅ {tier.title()} Plan Active")
    else:
        st.info("💫 Free Plan")
    
    # Usage metrics (existing code remains the same)
    usage_daily = st.session_state.usage.get('daily', 0)
    usage_monthly = st.session_state.usage.get('monthly', 0)
    limits = TIERS.get(tier, TIERS['free'])
    
    # Daily usage
    daily_percentage = min(usage_daily / limits['daily'], 1.0) if limits['daily'] != float('inf') else 0
    st.metric(
        "🔍 Daily Searches", 
        f"{usage_daily}/{limits['daily'] if limits['daily'] != float('inf') else '∞'}",
        delta=f"{daily_percentage:.0%} used"
    )
    if limits['daily'] != float('inf'):
        st.progress(daily_percentage)
    
    # Monthly usage
    monthly_percentage = min(usage_monthly / limits['monthly'], 1.0) if limits['monthly'] != float('inf') else 0
    st.metric(
        "🗓️ Monthly Searches", 
        f"{usage_monthly}/{limits['monthly'] if limits['monthly'] != float('inf') else '∞'}",
        delta=f"{monthly_percentage:.0%} used"
    )
    if limits['monthly'] != float('inf'):
        st.progress(monthly_percentage)
    
    # Reset times
    if st.session_state.get("reset"):
        reset = st.session_state.reset
        if "daily" in reset:
            st.caption(f"🔁 Daily resets {time_until(reset['daily'])}")
        if "monthly" in reset:
            st.caption(f"📅 Monthly resets {time_until(reset['monthly'])}")
    
    st.divider()
    
    # Session management
    if not st.session_state.premium:
        # Login section for premium users
        with st.expander("🔑 Premium Login"):
            st.info("Already have a premium subscription? Login here!")
            premium_key = st.text_input("Premium API Key", type="password", help="Enter your premium API key")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Login", type="primary"):
                    if not premium_key:
                        st.warning("Please enter your premium API key")
                    else:
                        try:
                            resp = requests.post(
                                f"{API_URL}/login",
                                json={"premium_key": premium_key},
                                headers={"X-API-Key": API_KEY}
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                if data.get("success"):
                                    st.session_state.premium = True
                                    st.session_state.premium_tier = data["tier"]
                                    st.success(f"✅ Logged in as {data['tier'].title()}!")
                                    st.balloons()
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Login failed: {data.get('error', 'Unknown error')}")
                            else:
                                try:
                                    error_data = resp.json()
                                    error_msg = error_data.get('error', 'Unknown error')
                                except:
                                    error_msg = resp.text[:200]
                                st.error(f"❌ Login failed ({resp.status_code}): {error_msg}")
                        except Exception as e:
                            st.error(f"🚨 Connection error: {str(e)}")
            
            with col2:
                st.markdown("**Need Premium?**")
                if st.button("💎 Activate New"):
                    st.session_state.show_activation = True
        
        # License activation (only show if clicked or no premium)
        if st.session_state.get("show_activation", False) or not st.session_state.get("premium_key_available", True):
            with st.expander("🎫 Activate New License", expanded=st.session_state.get("show_activation", False)):
                st.warning("⚠️ **New Subscription**: This will create a new premium API key tied to your current app API key.")
                license_key = st.text_input("License Key")
                if st.button("Activate License"):
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
                                    st.success(f"✅ Premium {data['tier'].title()} Activated!")
                                    st.info(f"🔑 **Your Premium API Key:** `{data['api_key']}`")
                                    st.warning("⚠️ **IMPORTANT**: Save this API key! Use it to login on any device.")
                                    
                                    # Auto-login with new key
                                    login_resp = requests.post(
                                        f"{API_URL}/login",
                                        json={"premium_key": data['api_key']},
                                        headers={"X-API-Key": API_KEY}
                                    )
                                    if login_resp.ok:
                                        st.session_state.premium = True
                                        st.session_state.premium_tier = data["tier"]
                                        st.session_state.show_activation = False
                                        st.balloons()
                                        time.sleep(3)
                                        st.rerun()
                                else:
                                    st.error(f"❌ Activation failed: {data.get('error', 'Unknown error')}")
                            else:
                                try:
                                    error_data = resp.json()
                                    error_msg = error_data.get('error', 'Unknown error')
                                except:
                                    error_msg = resp.text[:200]
                                st.error(f"❌ Activation failed ({resp.status_code}): {error_msg}")
                        except Exception as e:
                            st.error(f"🚨 Connection error: {str(e)}")
    else:
        # Premium session management
        with st.expander("🔑 Premium Session"):
            st.success(f"✅ Logged in as {tier.title()}")
            
            # Session info
            if st.session_state.get("reset", {}).get("monthly"):
                reset_date = st.session_state.reset["monthly"]
                st.metric("Session Active", "Yes")
                st.caption(f"Subscription resets {time_until(reset_date)}")
            
            st.divider()
            
            # Logout button
            if st.button("🚪 Logout", type="secondary", help="End premium session (you can login again anytime)"):
                try:
                    resp = requests.post(
                        f"{API_URL}/logout",
                        headers={"X-API-Key": API_KEY}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("success"):
                            st.session_state.premium = False
                            st.session_state.premium_tier = "free"
                            st.success("✅ Logged out successfully")
                            st.info("💡 You can login again anytime with your premium API key")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ Logout failed: {data.get('error', 'Unknown error')}")
                    else:
                        try:
                            error_data = resp.json()
                            error_msg = error_data.get('error', 'Unknown error')
                        except:
                            error_msg = resp.text[:200]
                        st.error(f"❌ Logout failed ({resp.status_code}): {error_msg}")
                except Exception as e:
                    st.error(f"🚨 Connection error: {str(e)}")
    


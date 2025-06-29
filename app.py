import streamlit as st
import pandas as pd
import requests
from io import StringIO

# ----------------- CONFIG -----------------
st.set_page_config(page_title="Cold Lead Scraper", layout="centered")

# ----------------- UI HEADER -----------------
st.title("🚀 Cold Lead Scraper & Email Extractor")
st.caption("Find local business leads with emails in seconds. Export to CSV. Powered by Google + AI.")

# ----------------- INPUT FIELDS -----------------
col1, col2 = st.columns([3, 1])
with col1:
    keyword = st.text_input("🔍 Business Type (e.g. plumber, dentist)", key="keyword")
with col2:
    location = st.text_input("📍 Location", key="location", value="Berlin")

# ----------------- FREE TIER LIMIT -----------------
MAX_FREE_SCRAPES = 3
if "free_uses" not in st.session_state:
    st.session_state["free_uses"] = 0

if st.session_state["free_uses"] >= MAX_FREE_SCRAPES:
    st.warning("🚫 Free tier limit reached (3 scrapes/day). [Upgrade to unlock unlimited access](https://yourgumroadlink.com)")
    st.stop()

# ----------------- SCRAPE BUTTON -----------------
leads = []
if st.button("🔍 Scrape Leads"):
    if not keyword or not location:
        st.error("Please enter both keyword and location.")
    else:
        st.session_state["free_uses"] += 1
        with st.spinner("Scraping leads..."):

            try:
                # Replace this with your actual API URL
                api_url = "https://74ea2c7f-2dfc-49b4-8aaf-8d4601db8782-00-nzsmwrqnnxdb.worf.replit.dev/scrape"
                headers = {"X-DEV-KEY": "letmein"}
                response = requests.post(api_url, json={"keyword": keyword, "location": location}, headers=headers)

                if response.status_code == 429:
                    st.warning(response.json().get("error", "Rate limit reached."))
                if response.status_code != 200:
                    st.error(f"❌ API Error: {response.status_code}")
                else:
                    leads = response.json()

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")

# ----------------- SHOW RESULTS -----------------
if leads:
    st.success(f"✅ {len(leads)} leads found!")
    for biz in leads:
        st.markdown(f"### 🏢 {biz.get('name', 'Unknown')}")
        st.write(f"📍 {biz.get('address', 'No address provided')}")

        if biz.get("email"):
            st.code(biz["email"])
            st.button("📋 Copy Email", key=f"copy-{biz['email']}")
        else:
            st.text("❌ No email found.")

        st.divider()

    # --------------- CSV DOWNLOAD ---------------
    df = pd.DataFrame(leads)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button("📥 Download Leads as CSV", csv_buffer.getvalue(), "leads.csv", mime="text/csv")

# ----------------- UPGRADE CTA -----------------
st.markdown("---")
st.markdown("🔓 Need more scrapes? [Upgrade to full version on Gumroad →](https://yourgumroadlink.com)", unsafe_allow_html=True)

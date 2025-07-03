import streamlit as st
import pandas as pd
import requests

API_URL = "https://cold-email-scraper.fly.dev/"  # Your backend URL

st.set_page_config(layout="wide", page_title="Cold Email Scraper", page_icon="📬")
st.title("📬 Cold Email Scraper")
st.caption("Find verified business leads (emails, phones, websites) from Google Places — export as CSV.")

# --- Input Form ---
with st.form("scrape_form"):
    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input("🔍 Business type", placeholder="e.g. dentist, gym")
    with col2:
        location = st.text_input("📍 Location", placeholder="e.g. London, Berlin")
    
    count = st.slider("How many results?", min_value=5, max_value=30, value=15, step=5)
    submit = st.form_submit_button("🚀 Scrape Leads")

# --- Scrape Logic ---
if submit:
    if not keyword or not location:
        st.warning("Please enter both keyword and location.")
    else:
        with st.spinner("Scraping... hang tight!"):
            try:
                response = requests.post(
                    API_URL + "scrape",
                    json={"keyword": keyword, "location": location, "count": count},
                    timeout=30
                )
                data = response.json()

                if "error" in data:
                    st.error(f"❌ {data['error']}")
                elif not data:
                    st.info("No leads found. Try another keyword/location.")
                else:
                    df = pd.DataFrame(data)
                    df = df[df["email"].notna() | df["phone"].notna()]
                    df = df[["name", "email", "phone", "website", "address", "rating", "hours"]]
                    df.columns = [col.title() for col in df.columns]

                    st.success(f"✅ Found {len(df)} leads ({df['Email'].notna().sum()} with email)")

                    # CSV
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "📥 Download as CSV",
                        data=csv,
                        file_name=f"{keyword}_{location}_leads.csv",
                        mime="text/csv"
                    )

                    st.dataframe(df, use_container_width=True)

            except Exception as e:
                st.error(f"Something went wrong: {e}")

st.markdown("---")
st.markdown("🔒 Want full access + bonus tools? [Get the SaaS bundle →](https://yourbundle.gumroad.com)")

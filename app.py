import streamlit as st
import pandas as pd
import requests

# --- CONFIG ---
API_URL = "https://cold-email-scraper.fly.dev/"  # Your backend URL

st.set_page_config(layout="wide", page_title="Cold Email Scraper", page_icon="📬")

st.markdown("""
    <style>
    @media only screen and (max-width: 768px) {
        .block-container { padding: 1rem; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("📬 Cold Email Scraper")
st.caption("Get emails, phones, and websites from local businesses — ready to cold email!")

# --- INPUT FORM ---
with st.form("scrape_form"):
    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input("🔍 Business type", placeholder="e.g. dentist, gym, bakery")
    with col2:
        location = st.text_input("📍 Location", placeholder="e.g. Berlin, London")
    
    count = st.slider("How many results?", 5, 30, 15, step=5)
    submit = st.form_submit_button("🚀 Scrape Leads")

# --- LOGIC ---
if submit:
    if not keyword or not location:
        st.warning("Please enter both fields.")
    else:
        with st.spinner("Scraping leads... hang tight!"):
            try:
                response = requests.post(
                    API_URL + "scrape",
                    json={"keyword": keyword, "location": location, "count": count},
                    timeout=25
                )
                data = response.json()

                if "error" in data:
                    st.error(f"❌ {data['error']}")
                elif not data:
                    st.info("No leads found. Try a broader search.")
                else:
                    df = pd.DataFrame(data)
                    df = df[["name", "email", "phone", "website", "address", "rating", "hours"]]
                    df = df.rename(columns=str.title)

                    emails_found = df["Email"].notna().sum()
                    st.success(f"✅ Found {len(df)} leads ({emails_found} with email)")

                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Download CSV", data=csv, file_name=f"{keyword}_{location}_leads.csv", mime="text/csv")

                    st.dataframe(df, use_container_width=True)

            except Exception as e:
                st.error(f"Something went wrong: {e}")

st.markdown("---")
st.markdown("🔓 [Unlock unlimited access & bonus tools →](https://yourbundle.gumroad.com)")

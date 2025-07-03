import streamlit as st
import pandas as pd
import requests

# --- CONFIG ---
API_URL = "https://cold-email-scraper.fly.dev/"  # Change to your backend base URL

st.set_page_config(page_title="Cold Email Scraper", layout="centered")
st.title("📬 Cold Email Scraper")
st.markdown("Get business leads (email, phone, website) from Google in seconds. Powered by AI scraping.")

# --- INPUT FORM ---
with st.form("scrape_form"):
    keyword = st.text_input("What kind of businesses are you targeting?", placeholder="e.g. dentist, gym, bakery")
    location = st.text_input("Where?", placeholder="e.g. London, New York, Berlin")
    submit = st.form_submit_button("🔍 Scrape")

if submit:
    if not keyword or not location:
        st.warning("Please enter both fields.")
    else:
        with st.spinner("Scraping leads... hang tight!"):
            try:
                response = requests.post(
                    API_URL + "scrape",
                    json={"keyword": keyword, "location": location}
                )
                data = response.json()

                if "error" in data:
                    st.error(f"❌ {data['error']}")
                elif not data:
                    st.info("No leads found. Try a broader keyword or location.")
                else:
                    df = pd.DataFrame(data)
                    st.success(f"✅ Found {len(df)} leads!")
                    df = df[["name", "email", "phone", "website", "address", "rating", "hours"]]
                    df = df.rename(columns=str.title)  # Optional: Make column names pretty
                    st.dataframe(df)

                    # CSV download
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download leads as CSV",
                        data=csv,
                        file_name=f"{keyword}_{location}_leads.csv",
                        mime="text/csv"
                    )

            except Exception as e:
                st.error(f"Something went wrong: {e}")

st.markdown("---")
st.markdown("🔒 Want unlimited access + 5 more tools? [Unlock the full SaaS bundle →](https://yourbundle.gumroad.com)")

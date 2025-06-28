import streamlit as st
import pandas as pd
import requests
import time

# --- CONFIG ---
API_URL = "https://74ea2c7f-2dfc-49b4-8aaf-8d4601db8782-00-nzsmwrqnnxdb.worf.replit.dev/scrape"  # Replace with your real URL

st.set_page_config(page_title="Cold Email Scraper", layout="centered")
st.title("📬 Cold Email Scraper")
st.markdown("Get business leads (email, phone, website) from Google in seconds. Powered by AI scraping.")

# --- INPUT FORM ---
with st.form("scrape_form"):
    keyword = st.text_input("What kind of businesses are you targeting?", placeholder="e.g. dentist, gym, bakery")
    location = st.text_input("Where?", placeholder="e.g. London, New York, Berlin")
    submit = st.button("Scrape", on_click=scrape_action, disabled=st.session_state['loading'])

if submit:
    if not keyword or not location:
        st.warning("Please enter both fields.")
    else:
        with st.spinner("Scraping leads... hang tight!"):
            try:
                response = requests.get(API_URL, params={"keyword": keyword, "location": location})
                st.text("Raw response:")
                st.text(response.text[:300])  # show first 300 chars
                data = response.json()

                if "error" in data:
                    st.error(f"❌ {data['error']}")
                elif not data:
                    st.info("No leads found. Try a broader keyword or location.")
                else:
                    df = pd.DataFrame(data)
                    st.success(f"✅ Found {len(df)} leads!")
                    # If 'hours' field is a list, convert it to comma-separated string
                    if 'hours' in df.columns:
                        df['hours'] = df['hours'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

# Show selected columns for better clarity
                    columns_to_show = ['name', 'website', 'phone', 'email', 'address', 'rating', 'hours']
                    available_cols = [col for col in columns_to_show if col in df.columns]
                    st.dataframe(df[available_cols])


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

import streamlit as st
import pandas as pd
import requests

# --- CONFIG ---
API_URL = "https://cold-email-scraper.fly.dev/"  # Change to your backend base URL

st.set_page_config(layout="wide", page_title="Cold Email Scraper", page_icon="📬")

st.markdown("""
    <style>
        /* Center form and results on mobile */
        @media only screen and (max-width: 768px) {
            .stTextInput > div > div,
            .stTextInput > label,
            .stButton > button {
                font-size: 16px !important;
            }
            .block-container {
                padding: 1rem;
            }
        }
        .css-18e3th9 { padding-top: 1rem; }  /* Fix top spacing */
    </style>
""", unsafe_allow_html=True)

# --- TITLE ---
st.title("📬 Cold Email Scraper")
st.caption("Find emails, phones & websites from Google-powered leads — fast, accurate, exportable.")

# --- FORM ---
with st.form("scrape_form"):
    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input("🔍 Business type", placeholder="e.g. dentist, gym, bakery")
    with col2:
        location = st.text_input("📍 Location", placeholder="e.g. London, New York, Berlin")
    
    submit = st.form_submit_button("🚀 Scrape Leads")

# --- SCRAPER LOGIC ---
if submit:
    if not keyword or not location:
        st.warning("Please enter both keyword and location.")
    else:
        with st.spinner("🔎 Scraping Google... hang tight!"):
            try:
                response = requests.post(
                    API_URL + "scrape",
                    json={"keyword": keyword, "location": location},
                    timeout=20
                )
                data = response.json()

                if "error" in data:
                    st.error(f"❌ {data['error']}")
                elif not data:
                    st.info("No leads found. Try a broader keyword or a nearby city.")
                else:
                    df = pd.DataFrame(data)
                    df = df[["name", "email", "phone", "website", "address", "rating", "hours"]]
                    df = df.rename(columns={
                        "name": "Name", "email": "Email", "phone": "Phone",
                        "website": "Website", "address": "Address",
                        "rating": "Rating", "hours": "Hours"
                    })

                    st.success(f"✅ Found {len(df)} leads!")

                    # CSV Download at top
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download leads as CSV",
                        data=csv,
                        file_name=f"{keyword}_{location}_leads.csv",
                        mime="text/csv"
                    )

                    st.dataframe(df, use_container_width=True)

            except Exception as e:
                st.error(f"Something went wrong: {e}")

# --- FOOTER ---
st.markdown("---")
st.markdown(
    "🔒 Want unlimited access + 5 more tools? "
    "[**Unlock the full SaaS bundle →**](https://yourbundle.gumroad.com)",
    unsafe_allow_html=True
)

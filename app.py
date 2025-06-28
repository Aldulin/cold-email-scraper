import streamlit as st
import pandas as pd
import requests
import time

if 'loading' not in st.session_state:
    st.session_state['loading'] = False
# --- CONFIG ---
API_URL = "https://74ea2c7f-2dfc-49b4-8aaf-8d4601db8782-00-nzsmwrqnnxdb.worf.replit.dev/scrape"  # Replace with your real URL

st.set_page_config(page_title="Cold Email Scraper", layout="centered")
st.title("📬 Cold Email Scraper")
st.markdown("Get business leads (email, phone, website) from Google in seconds. Powered by AI scraping.")

# --- INPUT FORM ---

keyword = st.text_input("What kind of businesses are you targeting?", placeholder="e.g. dentist, gym, bakery")
location = st.text_input("Where?", placeholder="e.g. London, New York, Berlin")
def scrape_action():
    st.session_state['loading'] = True
submit = st.button("Scrape", on_click=scrape_action, disabled=st.session_state['loading'])

if st.session_state['loading']:
    with st.spinner("Scraping leads... hang tight!"):
        progress_bar = st.progress(0)
    
        # Simulate progress over 3 seconds
        for i in range(30):
            time.sleep(0.1)  # wait 0.1 seconds
            progress_bar.progress((i + 1) * 100 // 30)

        try:
            response = requests.get(API_URL, params={"keyword": keyword, "location": location})
            data = response.json()

            progress_bar.progress(100)  # complete
            if "error" in data:
                st.error(f"❌ {data['error']}")
            elif not data:
                st.info("No leads found. Try a broader keyword or location.")
            else:
                df = pd.DataFrame(data)

                # Process 'hours' if list
                if 'hours' in df.columns:
                    df['hours'] = df['hours'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

                columns_to_show = ['name', 'website', 'phone', 'email', 'address', 'rating', 'hours']
                available_cols = [col for col in columns_to_show if col in df.columns]
                st.dataframe(df[available_cols])

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download leads as CSV",
                    data=csv,
                    file_name=f"{keyword}_{location}_leads.csv",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Something went wrong: {e}")

        # Reset loading state
        st.session_state['loading'] = False

#if submit:
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

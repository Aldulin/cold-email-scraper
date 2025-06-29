import streamlit as st
import requests
import pandas as pd
from io import StringIO

st.set_page_config(page_title="Cold Lead Scraper", layout="centered")

st.title("🚀 Cold Lead Scraper & Email Extractor")
st.caption("Find local business leads with emails in seconds. Export to CSV. Powered by Google + AI.")

col1, col2 = st.columns([3, 1])

with col1:
    keyword = st.text_input("🔍 Business Type (e.g. plumber, dentist)", key="keyword")

with col2:
    location = st.text_input("📍 Location", key="location", value="Berlin")

# Replace with your actual backend API URL
API_URL = "https://74ea2c7f-2dfc-49b4-8aaf-8d4601db8782-00-nzsmwrqnnxdb.worf.replit.dev/scrape"


# Initialize loading state
if 'loading' not in st.session_state:
    st.session_state['loading'] = False




# Define what happens when user clicks Scrape
def scrape_action():
    # Validate inputs before proceeding
    if not keyword.strip():
        st.warning("Please enter a keyword.")
        return
    if not location.strip():
        st.warning("Please enter a location.")
        return
    # Set loading to True to trigger scraping
    st.session_state['loading'] = True
    
    MAX_FREE_SCRAPES = 3
    if "free_uses" not in st.session_state:
        st.session_state["free_uses"] = 0

    if st.session_state["free_uses"] >= MAX_FREE_SCRAPES:
        st.warning("🚫 Free tier limit reached (3 scrapes/day). [Upgrade to unlock unlimited access](https://yourgumroadlink.com)")
        st.stop()
    if st.button("🔍 Scrape Leads"):
        if not keyword or not location:
            st.error("Please enter both keyword and location.")
        else:
            st.session_state["free_uses"] += 1
            # 🔁 Call your backend or scraper API here
            leads = call_your_backend(keyword, location)
    if leads:
        for biz in leads:
            st.markdown(f"### 🏢 {biz['name']}")
            st.write(f"📍 {biz.get('address', 'No address')}")
        
            if biz.get("email"):
                st.code(biz['email'])
                st.button("📋 Copy Email", key=f"copy-{biz['email']}")
            else:
                st.text("No email found ❌")

            st.divider()

# Scrape button - disabled when loading or inputs empty
   # submit = st.button(
    #    "Scrape",
     #   on_click=scrape_action,
     #   disabled=st.session_state['loading'] or not keyword.strip() or not location.strip()
      #   )

# When loading, perform scraping
    if st.session_state['loading']:
        with st.spinner("Scraping leads... hang tight!"):
            try:
            # Call backend API with user inputs
                response = requests.get(API_URL, params={"keyword": keyword, "location": location})

            # Handle rate limit HTTP status
                if response.status_code == 429:
                    st.error("🚫 Rate limit exceeded. Please wait a minute before trying again.")
                    st.session_state['loading'] = False
                    st.stop()

            # Raise exception for other bad statuses
                response.raise_for_status()
                data = response.json()

            # Handle error message from backend
                if "error" in data:
                    st.error(f"❌ {data['error']}")
            # Handle empty results
                elif not data:
                    st.info("No leads found. Try a broader keyword or location.")
                else:
                # Convert results to dataframe
                    df = pd.DataFrame(data)

                # Format 'hours' column if exists and is list
                    if 'hours' in df.columns:
                        df['hours'] = df['hours'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

                # Columns to display
                    columns_to_show = ['name', 'website', 'phone', 'email', 'address', 'rating', 'hours']
                    available_cols = [col for col in columns_to_show if col in df.columns]

                # Show results table
                    st.dataframe(df[available_cols])

                # Provide CSV download button
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download leads as CSV",
                        data=csv,
                        file_name=f"{keyword}_{location}_leads.csv",
                        mime="text/csv"
                    )
        
            except requests.exceptions.RequestException as e:
                st.error(f"Network error: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
            finally:
            # Reset loading state after done
                st.session_state['loading'] = False

    if leads:
        df = pd.DataFrame(leads)
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button("📥 Download Leads as CSV", csv_buffer.getvalue(), "leads.csv", mime="text/csv")

st.markdown("---")
st.markdown("🔓 Need more scrapes? [Upgrade to full version on Gumroad →](https://yourgumroadlink.com)", unsafe_allow_html=True)

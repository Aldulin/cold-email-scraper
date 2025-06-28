import streamlit as st
import requests
import pandas as pd

# Replace with your actual backend API URL
API_URL = "https://74ea2c7f-2dfc-49b4-8aaf-8d4601db8782-00-nzsmwrqnnxdb.worf.replit.dev/scrape"

# Initialize loading state
if 'loading' not in st.session_state:
    st.session_state['loading'] = False

# Input fields
keyword = st.text_input("Keyword")
location = st.text_input("Location")

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

# Scrape button - disabled when loading or inputs empty
submit = st.button(
    "Scrape",
    on_click=scrape_action,
    disabled=st.session_state['loading'] or not keyword.strip() or not location.strip()
)

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

        # Reset loading state after done
        st.session_state['loading'] = False

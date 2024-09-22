import streamlit as st
import requests
from bs4 import BeautifulSoup
import PyPDF2
import re
import pandas as pd
import time

# Function to extract Cloud Skill Boost IDs from a PDF
def extract_ids_from_pdf(uploaded_file):
    ids = []
    reader = PyPDF2.PdfReader(uploaded_file)
    for page in reader.pages:
        text = page.extract_text()
        if text:
            ids += re.findall(r'[a-f0-9\-]{36}', text)  # Matches UUID format
    return ids

# Function to check profile data
def check_profile(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract account creation year
        member_info = soup.find(string=lambda text: text and "Member since" in text)
        if member_info:
            year = member_info.split()[-1]
            
            # Extract username
            username_tag = soup.find('div', class_='ql-headline-2')
            username = username_tag.text.strip() if username_tag else "Unknown"
            
            profile_info = {
                "year": year,
                "url": url,
                "username": username,
                "badges": [],
                "is_eligible": False  # Added eligibility key
            }
            
            # Check if account is old (before 2024) or has badges
            if year == "2023":
                profile_info["status"] = "Old account"
                profile_info["is_eligible"] = False  # Old accounts are ineligible
            elif year == "2024":
                profile_info["status"] = "New account"
                profile_info["is_eligible"] = True  # New accounts are eligible
            else:
                profile_info["status"] = "Before 2023"
                profile_info["is_eligible"] = True  # Accounts before 2023 are eligible

            # Check for badges
            badges = soup.find_all(class_='profile-badge')
            if badges:
                profile_info["badges"] = [badge.find('span', class_='ql-title-medium l-mts').text for badge in badges]
                profile_info["has_badges"] = True
                if year == "2023":  # Old account but has badges
                    profile_info["is_eligible"] = False  # Ineligible due to being an old account
            else:
                profile_info["has_badges"] = False
            
            return profile_info
        else:
            return None
    else:
        return None

# Sidebar navigation
st.sidebar.title("Select Feature")
option = st.sidebar.selectbox("Choose a feature:", ["Cloud Skill Boost Profile Checker", "Automatic Form Fill"])

if option == "Cloud Skill Boost Profile Checker":
    st.title("GDG PIET - Cloud Skill Boost Profile Checker")
    st.markdown("<style> .hover {transition: all 0.3s ease;} .hover:hover {background-color: #f0f0f0;} </style>", unsafe_allow_html=True)

    # Manual link check
    st.subheader("Check a Single Profile Link")
    single_profile_link = st.text_input("Enter Profile Link", placeholder="https://www.cloudskillsboost.google/public_profiles/...")

    if st.button("Check Profile"):
        if single_profile_link:
            profile_info = check_profile(single_profile_link)
            if profile_info:
                st.success("Profile Found!", icon="✅")
                eligibility_status = "Ineligible" if not profile_info["is_eligible"] else "Eligible"
                st.markdown(f"""
                    <div style="border: 2px solid #007bff; padding: 15px; border-radius: 8px; background-color: #e9f5ff; color: #333;">
                        <strong style="color: #0056b3;">Username:</strong> {profile_info['username']}<br>
                        <strong style="color: #0056b3;">Profile URL:</strong> <a href="{profile_info['url']}" target="_blank" style="color: #007bff; text-decoration: none;">{profile_info['url']}</a><br>
                        <strong style="color: #0056b3;">Status:</strong> {profile_info['status']}<br>
                        <strong style="color: #0056b3;">Year Created:</strong> {profile_info['year']}<br>
                        <strong style="color: #0056b3;">Badges Earned:</strong> {', '.join(profile_info['badges']) if profile_info['badges'] else 'None'}<br>
                        <strong style="color: #0056b3;">Eligibility:</strong> {eligibility_status}
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Profile not found or invalid link.", icon="🚫")

    # Bulk check using file upload
    st.subheader("Bulk Check Profiles")
    uploaded_file = st.file_uploader("Upload PDF, CSV, or Excel file", type=["pdf", "csv", "xlsx"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".pdf"):
            # Process PDF file
            ids = extract_ids_from_pdf(uploaded_file)
        elif uploaded_file.name.endswith(".csv"):
            # Process CSV file
            df = pd.read_csv(uploaded_file)
            ids = df.iloc[:, 0].tolist()  # Assuming IDs are in the first column
        elif uploaded_file.name.endswith(".xlsx"):
            # Process Excel file
            df = pd.read_excel(uploaded_file)
            ids = df.iloc[:, 0].tolist()  # Assuming IDs are in the first column

        if ids:
            st.write("Processing profiles...Estimated Time for 100 responses is around 1min")
            time.sleep(1)  # Simulate processing delay
            
            results = []
            invalid_ids = []
            for profile_id in set(ids):  # Remove duplicates
                profile_url = f'https://www.cloudskillsboost.google/public_profiles/{profile_id}'
                profile_info = check_profile(profile_url)
                if profile_info:
                    if profile_info["year"] == "2023" or profile_info["has_badges"]:
                        results.append(profile_info)
                else:
                    invalid_ids.append(profile_id)  # Track invalid IDs

            # Display results
            st.subheader("Results Analysis:")
            st.write(f"Total accounts processed: {len(ids)}")
            st.write(f"Total ineligible accounts: {len(results)}")
            st.write(f"Total invalid accounts: {len(invalid_ids)}")  # Show count of invalid accounts

            if invalid_ids:
                st.markdown("### Invalid Accounts:")
                for profile_id in invalid_ids:
                    st.markdown(f"""
                        <div style="border: 2px solid #ff0000; padding: 10px; border-radius: 5px; background-color: #ffe6e6; color: #333;">
                            <strong style="color: #ff0000;">Invalid Profile ID:</strong> {profile_id}
                        </div>
                    """, unsafe_allow_html=True)

            if results:
                st.markdown("### Ineligible Accounts:")
                for result in results:
                    st.markdown(f"""
                        <div style="border: 2px solid #007bff; padding: 10px; border-radius: 5px; background-color: #e9f7ff; color: #333;">
                            <strong style="color: #007bff;">Username:</strong> {result['username']}<br>
                            <strong style="color: #007bff;">Profile URL:</strong> <a href="{result['url']}" target="_blank" style="color: #007bff; text-decoration: none;">{result['url']}</a><br>
                            <strong style="color: #007bff;">Status:</strong> <span style="color: {'green' if result['status'] == 'Old account' else 'red'};">{result['status']}</span><br>
                            <strong style="color: #007bff;">Year Created:</strong> <span style="color: #555;">{result['year']}</span><br>
                            <strong style="color: #007bff;">Badges Earned:</strong> <span style="color: #555;">{', '.join(result['badges']) if result['badges'] else 'None'}</span>
                        </div>
                    """, unsafe_allow_html=True)

            else:
                st.write("No valid accounts found.")
        else:
            st.write("No valid Cloud Skill Boost IDs found in the uploaded file.")

elif option == "Automatic Form Fill":
    st.title("Automatic Form Fill")
    st.markdown("Upload a CSV file containing the data to automatically fill forms.")
    
    csv_file = st.file_uploader("Upload CSV", type="csv")
    if csv_file is not None:
        df = pd.read_csv(csv_file)
        st.write("Data Preview:")
        st.dataframe(df)

        # Here you can implement your form-filling logic
        st.write("Form filling logic will go here.")

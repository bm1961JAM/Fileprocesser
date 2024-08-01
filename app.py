import streamlit as st
from openai import OpenAI
import os
import shutil
import PyPDF2
import pandas as pd
import json
import numpy as np
from zipfile import ZipFile
import requests
import bcrypt
import base64
from styles_and_html import get_page_bg_and_logo_styles

api_key = st.secrets["general"]["OPENAI_API_KEY"]
if not api_key:
    st.error("API key not found. Please set the OPENAI_API_KEY environment variable.")
    st.stop()

client = OpenAI(api_key=api_key)

# Function to read PDF content
def read_pdf(file_path):
    content = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page_num in range(len(reader.pages)):
            content += reader.pages[page_num].extract_text()
    return content

# Function to run a GPT task
def run_gpt_task(instructions, prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": prompt}
        ],
        max_tokens=4000
    )
    return response.choices[0].message.content

# Load instructions from JSON file
with open('instructions.json', 'r') as f:
    instructions = json.load(f)

# Load prompts from JSON file
with open('prompts.json', 'r') as f:
    prompts = json.load(f)

# Create a folder to save uploaded files if it doesn't exist
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Create a folder to save processed files if it doesn't exist
if not os.path.exists("processed"):
    os.makedirs("processed")

# Create a subfolder inside processed to store output files
output_folder = os.path.join("processed", "output_files")
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

if 'user_data' not in st.session_state:
    st.session_state['user_data'] = {'usernames': [], 'passwords': []}

def add_user():
    predefined_users = {
        "bm1961": "Charlotte-182"}

    for username, password in predefined_users.items():
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        st.session_state['user_data']['usernames'].append(username)
        st.session_state['user_data']['passwords'].append(hashed_password)

# Get the styles and HTML for the background and logo
page_bg_img, logo_html = get_page_bg_and_logo_styles()

# Apply CSS and HTML
st.markdown(page_bg_img, unsafe_allow_html=True)
st.markdown(logo_html, unsafe_allow_html=True)

st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        background-color: white;
        border-radius: 10px;
        border: 1px solid white;
        gap: 6px;
        padding-top: 15px;
        padding-bottom: 15px;
        color: black !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: white;
        color: black !important;
    }
    .stMarkdown, .stTextInput, .stHeader, .stTitle, .stSubheader, .stCaption, .stText, .stExpander, .stDownloadButton, .stException {
        color: white !important;
        background-color: transparent !important;
        border-radius: 10px;
        padding: 10px;
    }
    .stTextInput > label, .stTextInput > div, .stTextInput > label > div {
        color: white !important;
    }
    .stButton button {
        color: black !important;
    }
    .stBox {
        border: 1px solid white;
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
        background-color: transparent;
        color: white !important;
    }
    .css-1l7r3cz, .css-1d391kg, .css-hxt7ib, .css-18e3th9, .css-1aehpv1, .css-2trqyj, .css-1v3fvcr, .css-1cpxqw2, .css-12oz5g7, .css-1v0mbdj {
        color: white !important;
        background-color: transparent !important;
        border-radius: 10px;
    }
    .css-1g6gooi {
        display: none;
    }
    .stDownloadButton > button {
        color: black !important;
        margin-top: 20px;
        display: block;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown("<h1 style='color:white;'>Document Analysis and Processing</h1>", unsafe_allow_html=True)
    # Tabs: Upload documents and specify company name, Run GPT Tasks, Upload CSV Files, Download Specific Outputs, Upload Pillar Page
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Upload Required Documents", 
        "Execute GPT Tasks", 
        "Process and Analyze CSV Files", 
        "Generate Website Content", 
        "Create Pillar Page", 
        "Download & Overwrite Files"
    ])

    with tab1:
        st.markdown("<h1 style='color:white;'>Step 1: Upload Required Documents</h1>", unsafe_allow_html=True)
        st.markdown("""
            <p>In this step, you need to upload the workshop documents for analysis.</p>
            <p>The system will save the uploaded documents for further processing in the subsequent steps as inputs for the model.</p>
        """, unsafe_allow_html=True)
        company_name = st.text_input("Specify the company name")

        required_files = [
            "product_list.pdf",
            "USP.pdf",
            "key_stats.pdf",
            "about_us.pdf",
            "colour_scheme.pdf"
        ]

        uploaded_files = {}
        for file in required_files:
            file_path = os.path.join("uploads", f"{company_name}_{file}")
            if not os.path.exists(file_path):
                uploaded_files[file] = st.file_uploader(f"Upload {file}", type="pdf")
            else:
                uploaded_files[file] = None  # File already exists

        if st.button("Upload Documents"):
            if company_name:
                all_files_uploaded = True
                for file_name, uploaded_file in uploaded_files.items():
                    if uploaded_file is not None:
                        with open(os.path.join("uploads", f"{company_name}_{file_name}"), "wb") as f:
                            f.write(uploaded_file.getbuffer())
                    elif not os.path.exists(os.path.join("uploads", f"{company_name}_{file_name}")):
                        all_files_uploaded = False
                        st.error(f"File {file_name} not found. Please upload it.")

                if all_files_uploaded:
                    st.success("Files uploaded successfully!")
                else:
                    st.error("Please upload all required documents.")
            else:
                st.error("Please specify the company name.")

        # Add download button for this tab's files
        if os.path.exists("uploads"):
            with ZipFile(os.path.join("processed", f"{company_name}_uploads.zip"), "w") as zipf:
                for file_name in required_files:
                    file_path = os.path.join("uploads", f"{company_name}_{file_name}")
                    if os.path.exists(file_path):
                        zipf.write(file_path, file_name)
            with open(os.path.join("processed", f"{company_name}_uploads.zip"), "rb") as zipf:
                st.download_button(
                    label="Download Uploaded Documents",
                    data=zipf,
                    file_name=f"{company_name}_uploads.zip"
                )

    with tab2:
        st.markdown("<h1 style='color:white;'>Step 2: Execute GPT Tasks</h1>", unsafe_allow_html=True)
        st.markdown("""
            <p>In this step, you will run GPT tasks to process the uploaded documents. </p>
            <p>Outcome: The system will then generate outputs such as buyer persona, mission statement, brand voice, SEO summaries, and keywords for further research.</p>
        """, unsafe_allow_html=True)

        if st.button("Run GPT Tasks"):
            if company_name:
                document_contents = {}
                all_files_present = True
                for file_name in required_files:
                    file_path = os.path.join("uploads", f"{company_name}_{file_name}")
                    if os.path.exists(file_path):
                        document_contents[file_name] = read_pdf(file_path)
                    else:
                        st.error(f"File {file_name} not found. Please upload it in the first tab.")
                        all_files_present = False
                        break

                if all_files_present:
                    # Separate document texts
                    product_list_text = document_contents.get("product_list.pdf", "")
                    USP_text = document_contents.get("USP.pdf", "")
                    key_stats_text = document_contents.get("key_stats.pdf", "")
                    about_us_text = document_contents.get("about_us.pdf", "")
                    colour_scheme_text = document_contents.get("colour_scheme.pdf", "")

                    # 1. Buyer Persona
                    prompt_buyer_persona = prompts["prompt_buyer_persona"].format(company_name=company_name, product_list=product_list_text, USP=USP_text, key_stats=key_stats_text, about_us=about_us_text)
                    buyer_persona = run_gpt_task(instructions["buyer_persona"], prompt_buyer_persona)
                    with open(os.path.join("processed", f"{company_name}_buyer_persona.txt"), "w") as f:
                        f.write(buyer_persona)

                    # 2. English Editor for Buyer Persona
                    prompt_english_editor = prompts["prompt_english_editor"].format(file_name=f"{company_name}_buyer_persona.txt", file_content=buyer_persona)
                    english_editor_output = run_gpt_task(instructions["english_editor"], prompt_english_editor)
                    with open(os.path.join("processed", f"{company_name}_buyer_persona.txt"), "w") as f:
                        f.write(english_editor_output)

                    # 3. Mission Statement
                    prompt_mission_statement = prompts["prompt_mission_statement"].format(company_name=company_name, product_list=product_list_text, USP=USP_text, key_stats=key_stats_text, about_us=about_us_text, buyer_persona=buyer_persona)
                    mission_values = run_gpt_task(instructions["mission_statement"], prompt_mission_statement)
                    with open(os.path.join("processed", f"{company_name}_mission_values.txt"), "w") as f:
                        f.write(mission_values)

                    # 4. English Editor for Mission Values
                    prompt_english_editor_mission = prompts["prompt_english_editor"].format(file_name=f"{company_name}_mission_values.txt", file_content=mission_values)
                    english_editor_mission_output = run_gpt_task(instructions["english_editor"], prompt_english_editor_mission)
                    with open(os.path.join("processed", f"{company_name}_mission_values.txt"), "w") as f:
                        f.write(english_editor_mission_output)

                    # 5. SEO Summarizer
                    prompt_seo_summarizer = prompts["prompt_seo_summarizer"].format(product_list=product_list_text, USP=USP_text, key_stats=key_stats_text, about_us=about_us_text, buyer_persona=buyer_persona)
                    seo_summarizer_output = run_gpt_task(instructions["seo_summarizer"], prompt_seo_summarizer)
                    with open(os.path.join("processed", f"{company_name}_seo_summarizer.txt"), "w") as f:
                        f.write(seo_summarizer_output)

                    # 6. English Editor for SEO Summarizer
                    prompt_english_editor_seo = prompts["prompt_english_editor"].format(file_name=f"{company_name}_seo_summarizer.txt", file_content=seo_summarizer_output)
                    english_editor_seo_output = run_gpt_task(instructions["english_editor"], prompt_english_editor_seo)
                    with open(os.path.join("processed", f"{company_name}_seo_summarizer.txt"), "w") as f:
                        f.write(english_editor_seo_output)

                    # 7. SEO Keywords
                    prompt_magic_words = prompts["prompt_magic_words"].format(english_editor_seo_output=english_editor_seo_output)
                    seo_keywords = run_gpt_task(instructions["magic_words"], prompt_magic_words)
                    with open(os.path.join("processed", f"{company_name}_seo_keywords.txt"), "w") as f:
                        f.write(seo_keywords)
                     # Brand Voice   
                    prompt_brand_voice = prompts["prompt_brand_voice"].format(company_name=company_name, product_list=product_list_text, USP=USP_text, key_stats=key_stats_text, about_us=about_us_text, buyer_persona=buyer_persona, mission_values=mission_values)
                    brand_voice = run_gpt_task(instructions["brand_voice"], prompt_brand_voice)
                    with open(os.path.join("processed", f"{company_name}_brand_voice.txt"), "w") as f:
                        f.write(brand_voice)
    
                    prompt_english_editor_brand = prompts["prompt_english_editor"].format(file_name=f"{company_name}_brand_voice.txt", file_content=brand_voice)
                    english_editor_brand_output = run_gpt_task(instructions["english_editor"], prompt_english_editor_brand)
                    with open(os.path.join("processed", f"{company_name}_brand_voice.txt"), "w") as f:
                        f.write(english_editor_brand_output)

                    # Zip the specific output files for download
                    with ZipFile(os.path.join("processed", f"{company_name}_specific_outputs_gpt_tasks.zip"), "w") as zipf:
                        zipf.write(os.path.join("processed", f"{company_name}_buyer_persona.txt"), f"{company_name}_buyer_persona.txt")
                        zipf.write(os.path.join("processed", f"{company_name}_mission_values.txt"), f"{company_name}_mission_values.txt")
                        zipf.write(os.path.join("processed", f"{company_name}_seo_summarizer.txt"), f"{company_name}_seo_summarizer.txt")
                        zipf.write(os.path.join("processed", f"{company_name}_seo_keywords.txt"), f"{company_name}_seo_keywords.txt")
                        zipf.write(os.path.join("processed", f"{company_name}_brand_voice.txt"), f"{company_name}_brand_voice.txt")

                    st.success("GPT tasks have been executed and files are zipped!")

        # Add download button for this tab's files
        if os.path.exists("processed"):
            with ZipFile(os.path.join("processed", f"{company_name}_gpt_tasks.zip"), "w") as zipf:
                for file in ["buyer_persona.txt", "mission_values.txt", "seo_summarizer.txt", "seo_keywords.txt"]:
                    file_path = os.path.join("processed", f"{company_name}_{file}")
                    if os.path.exists(file_path):
                        zipf.write(file_path, file)
            with open(os.path.join("processed", f"{company_name}_gpt_tasks.zip"), "rb") as zipf:
                st.download_button(
                    label="Download GPT Task Outputs",
                    data=zipf,
                    file_name=f"{company_name}_gpt_tasks.zip"
                )

    with tab3:
        st.markdown("<h1 style='color:white;'>Step 3: Process and Analyze CSV Files</h1>", unsafe_allow_html=True)
        st.markdown("""
            <p>In this step, you need to upload CSV files for processing and analysis. The system will analyze the CSV files and generate a list of top 150 keywords based on various criteria.</p>
            <p>Outcome: The system will process the CSV files and generate a file containing the top 150 keywords.</p>
        """, unsafe_allow_html=True)

        csv_files = st.file_uploader("Upload CSV files", type="csv", accept_multiple_files=True)

        if csv_files and st.button("Process CSV Files"):
            if company_name:
                csv_file_paths = []
                for i, file in enumerate(csv_files):
                    file_path = os.path.join("uploads", f"{company_name}_csv_file_{i + 1}.csv")
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                    csv_file_paths.append(file_path)

                if csv_file_paths:
                    # Load the CSV files
                    dataframes = []
                    for i, file_path in enumerate(csv_file_paths):
                        df = pd.read_csv(file_path)
                        df['Source'] = f'{company_name}_csv_file_{i + 1}'  # Add source column with company name
                        dataframes.append(df)

                    # Concatenate the dataframes
                    combined_df = pd.concat(dataframes, ignore_index=True)

                    # Data cleaning
                    combined_df['Volume'] = pd.to_numeric(combined_df['Volume'], errors='coerce').fillna(0)
                    combined_df['Keyword Difficulty'] = pd.to_numeric(combined_df['Keyword Difficulty'], errors='coerce').fillna(100)
                    combined_df['CPC (GBP)'] = pd.to_numeric(combined_df['CPC (GBP)'], errors='coerce').fillna(0)

                    # Filter and score
                    combined_df = combined_df[(combined_df['Volume'] >= 20) | 
                                            (combined_df['CPC (GBP)'] >= 0.35) | 
                                            ((combined_df['Keyword Difficulty'] <= 50) & 
                                            (combined_df['Keyword Difficulty'] >= 10)) | 
                                            (combined_df['Keyword Difficulty'].isna())]
                    combined_df['Score'] = np.log(combined_df['Volume']) / combined_df['CPC (GBP)']

                    # Select top 150 keywords
                    top_keywords_list = []
                    remaining_slots = 150
                    for source, group in combined_df.groupby('Source'):
                        group_top = group.nlargest(15, 'Score')
                        top_keywords_list.append(group_top)
                        remaining_slots -= len(group_top)
                        if remaining_slots <= 0:
                            break

                    if remaining_slots > 0:
                        remaining_keywords = combined_df[~combined_df.index.isin(pd.concat(top_keywords_list).index)]
                        additional_keywords = remaining_keywords.nlargest(remaining_slots, 'Score')
                        top_keywords_list.append(additional_keywords)

                    top_keywords = pd.concat(top_keywords_list).nlargest(150, 'Score')['Keyword']

                    # Save the top keywords
                    output_file = os.path.join("processed", f"{company_name}_top_150_keywords.csv")
                    top_keywords.to_csv(output_file, index=False)

                    st.success("CSV files processed and top 150 keywords saved!")
                    # with open(output_file, "rb") as f:
                    #     st.download_button("Download Top 150 Keywords", f, file_name=f"{company_name}_top_150_keywords.csv")
                else:
                    st.error("No CSV files found.")
            else:
                st.error("Please specify the company name in the first tab.")

        # Add download button for this tab's files
        if os.path.exists("processed"):
            with ZipFile(os.path.join("processed", f"{company_name}_csv_analysis.zip"), "w") as zipf:
                file_path = os.path.join("processed", f"{company_name}_top_150_keywords.csv")
                if os.path.exists(file_path):
                    zipf.write(file_path, "top_150_keywords.csv")
            with open(os.path.join("processed", f"{company_name}_csv_analysis.zip"), "rb") as zipf:
                st.download_button(
                    label="Download CSV Analysis Outputs",
                    data=zipf,
                    file_name=f"{company_name}_csv_analysis.zip"
                )

    with tab4:
        st.markdown("<h1 style='color:white;'>Step 4: Generate Website Content</h1>", unsafe_allow_html=True)
        st.markdown("""
            <p>In this step, you will generate topic clusters, website structure, and web page content based on uploaded documents and processed data.</p>
        """, unsafe_allow_html=True)

        if st.button("Generate Website Content"):
            if company_name:
                document_contents = {}
                for file_name in required_files:
                    file_path = os.path.join("uploads", f"{company_name}_{file_name}")
                    if os.path.exists(file_path):
                        document_contents[file_name] = read_pdf(file_path)

                product_list_text = document_contents.get("product_list.pdf", "")
                USP_text = document_contents.get("USP.pdf", "")
                key_stats_text = document_contents.get("key_stats.pdf", "")
                about_us_text = document_contents.get("about_us.pdf", "")
                colour_scheme_text = document_contents.get("colour_scheme.pdf", "")
                colour_scheme_text = document_contents.get("brand_voice.pdf", "")

                with open(os.path.join("processed", f"{company_name}_buyer_persona.txt"), "r") as f:
                    buyer_persona = f.read()
                with open(os.path.join("processed", f"{company_name}_top_150_keywords.csv"), "r") as f:
                    top_keywords = f.read()
                with open(os.path.join("processed", f"{company_name}_mission_values.txt"), "r") as f:
                    mission_values = f.read()

                # 1. Topic Cluster Analysis
                prompt_topic_cluster = prompts["prompt_topic_cluster"].format(company_name=company_name, product_list=product_list_text,  buyer_persona=buyer_persona, seo_keywords=top_keywords)
                topic_cluster_document = run_gpt_task(instructions["topic_cluster"], prompt_topic_cluster)
                with open(os.path.join("processed", f"{company_name}_topic_cluster_document.txt"), "w") as f:
                    f.write(topic_cluster_document)

                prompt_extract_keywords = prompts["prompt_extract_keywords"].format(topic_cluster_document=topic_cluster_document)
                keywords = run_gpt_task(instructions["editor"], prompt_extract_keywords)
                with open(os.path.join("processed", f"{company_name}_keywords.txt"), "w") as f:
                    f.write(keywords)

                prompt_website_structure = prompts["prompt_website_structure"].format(company_name=company_name, product_list=product_list_text, USP=USP_text, key_stats=key_stats_text, about_us=about_us_text, buyer_persona=buyer_persona, topic_cluster_document=topic_cluster_document, keywords=keywords)
                website_structure_document = run_gpt_task(instructions["website_structure"], prompt_website_structure)
                with open(os.path.join("processed", f"{company_name}_website_structure_document.txt"), "w") as f:
                    f.write(website_structure_document)

                prompt_extract_home_page = prompts["prompt_extract_home_page"].format(website_structure_document=website_structure_document)
                home_page_structure = run_gpt_task(instructions["editor"], prompt_extract_home_page)

                with open(os.path.join("processed", f"{company_name}_brand_voice.txt"), "r") as f:
                    brand_voice_text = f.read()
                with open(os.path.join("processed", f"{company_name}_keywords.txt"), "r") as f:
                    keywords = f.read()

                prompt_home_page = prompts["prompt_home_page"].format(company_name=company_name, product_list=product_list_text, USP=USP_text, key_stats=key_stats_text, about_us=about_us_text, brand_voice_text=brand_voice_text, keywords=keywords)
                home_page_document = run_gpt_task(instructions["home_page"], prompt_home_page)
                with open(os.path.join("processed", f"{company_name}_home_page.txt"), "w") as f:
                    f.write(home_page_document)

                prompt_english_editor_home = prompts["prompt_english_editor"].format(file_name=f"{company_name}_home_page.txt", file_content=home_page_document)
                home_page_final = run_gpt_task(instructions["english_editor"], prompt_english_editor_home)
                with open(os.path.join("processed", f"{company_name}_home_page_final.txt"), "w") as f:
                    f.write(home_page_final)

                prompt_extract_about_us = prompts["prompt_extract_about_us"].format(website_structure_document=website_structure_document)
                about_us_structure = run_gpt_task(instructions["editor"], prompt_extract_about_us)

                prompt_about_us = prompts["prompt_about_us"].format(company_name=company_name, product_list=product_list_text, USP=USP_text, key_stats=key_stats_text, about_us=about_us_text,  brand_voice_text=brand_voice_text, keywords=keywords)
                about_us_document = run_gpt_task(instructions["about_us"], prompt_about_us)
                with open(os.path.join("processed", f"{company_name}_about_us.txt"), "w") as f:
                    f.write(about_us_document)

                prompt_english_editor_about_us = prompts["prompt_english_editor"].format(file_name=f"{company_name}_about_us.txt", file_content=about_us_document)
                about_us_final = run_gpt_task(instructions["english_editor"], prompt_english_editor_about_us)
                with open(os.path.join("processed", f"{company_name}_about_us_final.txt"), "w") as f:
                    f.write(about_us_final)

                # Zip the specific outputs for download
                with ZipFile(os.path.join("processed", f"{company_name}_specific_outputs_website_content.zip"), "w") as zipf:
                    zipf.write(os.path.join("processed", f"{company_name}_topic_cluster_document.txt"), f"{company_name}_topic_cluster_document.txt")
                    zipf.write(os.path.join("processed", f"{company_name}_keywords.txt"), f"{company_name}_keywords.txt")
                    zipf.write(os.path.join("processed", f"{company_name}_website_structure_document.txt"), f"{company_name}_website_structure_document.txt")
                    zipf.write(os.path.join("processed", f"{company_name}_home_page.txt"), f"{company_name}_home_page.txt")
                    zipf.write(os.path.join("processed", f"{company_name}_home_page_final.txt"), f"{company_name}_home_page_final.txt")
                    zipf.write(os.path.join("processed", f"{company_name}_about_us.txt"), f"{company_name}_about_us.txt")
                    zipf.write(os.path.join("processed", f"{company_name}_about_us_final.txt"), f"{company_name}_about_us_final.txt")

                st.success("Website content has been generated and zipped!")

        # Add download button for this tab's files
        if os.path.exists("processed"):
            with ZipFile(os.path.join("processed", f"{company_name}_website_content.zip"), "w") as zipf:
                for file in ["topic_cluster_document.txt", "keywords.txt", "website_structure_document.txt", "brand_voice.txt", "home_page.txt", "home_page_final.txt", "about_us.txt", "about_us_final.txt"]:
                    file_path = os.path.join("processed", f"{company_name}_{file}")
                    if os.path.exists(file_path):
                        zipf.write(file_path, file)
            with open(os.path.join("processed", f"{company_name}_website_content.zip"), "rb") as zipf:
                st.download_button(
                    label="Download Website Content Outputs",
                    data=zipf,
                    file_name=f"{company_name}_website_content.zip"
                )

    with tab5:
        st.markdown("<h1 style='color:white;'>Step 5: Create Pillar Page</h1>", unsafe_allow_html=True)
        st.markdown("""
            <p>In this step, you will enter the content or upload a Pillar Page PDF document.</p>
            <p>Outcome: The system will generate and edit the content of the pillar page based on the provided text or document.</p>
        """, unsafe_allow_html=True)

        # Text input for prompt
        pillar_page_text = st.text_area("Enter the content for the Pillar Page")

        # Option to upload a PDF as before
        pillar_page_file = st.file_uploader("Or upload a Pillar Page PDF", type="pdf")

        # Process the entered text or uploaded PDF
        if pillar_page_file:
            pillar_page_path = os.path.join("uploads", f"{company_name}_pillar_page.pdf")
            with open(pillar_page_path, "wb") as f:
                f.write(pillar_page_file.getbuffer())

            pillar_page_content = read_pdf(pillar_page_path)
        else:
            pillar_page_content = pillar_page_text

        if st.button("Process Pillar Page"):
            if company_name:
                # Read content from the saved PDFs
                document_contents = {}
                for file_name in required_files:
                    file_path = os.path.join("uploads", f"{company_name}_{file_name}")
                    if os.path.exists(file_path):
                        document_contents[file_name] = read_pdf(file_path)

                # Separate document texts
                product_list_text = document_contents.get("product_list.pdf", "")
                USP_text = document_contents.get("USP.pdf", "")
                key_stats_text = document_contents.get("key_stats.pdf", "")
                about_us_text = document_contents.get("about_us.pdf", "")
                colour_scheme_text = document_contents.get("colour_scheme.pdf", "")

                # Read the existing files
                with open(os.path.join("processed", f"{company_name}_buyer_persona.txt"), "r") as f:
                    buyer_persona = f.read()
                with open(os.path.join("processed", f"{company_name}_top_150_keywords.csv"), "r") as f:
                    top_keywords = f.read()
                with open(os.path.join("processed", f"{company_name}_mission_values.txt"), "r") as f:
                    mission_values = f.read()
                with open(os.path.join("processed",f"{company_name}_brand_voice.txt"), "r") as f:
                    brand_voice = f.read()
                with open(os.path.join("processed", f"{company_name}_keywords.txt"), "r") as f:
                    keywords = f.read()

                # Ensure pillar_page_content is read only if pillar_page_file was uploaded
                if pillar_page_file:
                    pillar_page_content = read_pdf(pillar_page_path)

                # Generate the prompt for the pillar page
                prompt_pillar_page = prompts["prompt_pillar_page"].format(
                    company_name=company_name, 
                    pillar_page_content=pillar_page_content, 
                    product_list=product_list_text, 
                    USP=USP_text, 
                    key_stats=key_stats_text, 
                    about_us=about_us_text, 
                    brand_voice_text=brand_voice, 
                    keywords=keywords
                )
                pillar_page_document = run_gpt_task(instructions["pillar_page"], prompt_pillar_page)
                with open(os.path.join("processed", f"{company_name}_pillar_page.txt"), "w") as f:
                    f.write(pillar_page_document)

                # English Editor for Pillar Page
                prompt_english_editor_pillar = prompts["prompt_english_editor"].format(file_name=f"{company_name}_pillar_page.txt", file_content=pillar_page_document)
                pillar_page_final = run_gpt_task(instructions["english_editor"], prompt_english_editor_pillar)
                with open(os.path.join("processed", f"{company_name}_pillar_page_final.txt"), "w") as f:
                    f.write(pillar_page_final)

                # Zip the pillar page files for download
                with ZipFile(os.path.join("processed", f"{company_name}_specific_outputs_pillar_page.zip"), "w") as zipf:
                    zipf.write(os.path.join("processed", f"{company_name}_pillar_page.txt"), f"{company_name}_pillar_page.txt")
                    zipf.write(os.path.join("processed", f"{company_name}_pillar_page_final.txt"), f"{company_name}_pillar_page_final.txt")

                st.success("Pillar page has been processed and edited!")

        # Add download button for this tab's files
        if os.path.exists("processed"):
            with ZipFile(os.path.join("processed", f"{company_name}_pillar_page.zip"), "w") as zipf:
                for file in ["pillar_page.txt", "pillar_page_final.txt"]:
                    file_path = os.path.join("processed", f"{company_name}_{file}")
                    if os.path.exists(file_path):
                        zipf.write(file_path, file)
            with open(os.path.join("processed", f"{company_name}_pillar_page.zip"), "rb") as zipf:
                st.download_button(
                    label="Download Pillar Page Outputs",
                    data=zipf,
                    file_name=f"{company_name}_pillar_page.zip"
                )

    with tab6:
        st.markdown("<h1 style='color:white;'>Step 6: Download & Overwrite Files</h1>", unsafe_allow_html=True)
        st.markdown("""
            <p>In this step, you can download and re-upload processed files for further editing.</p>
            <p>Outcome: The system allows you to download the generated files and re-upload any edited versions.</p>
        """, unsafe_allow_html=True)

        if company_name:
            file_dict = {}

            # Scan the 'processed' folder for files
            for root, dirs, files in os.walk("processed"):
                for file in files:
                    if company_name in file:
                        file_path = os.path.join(root, file)
                        base_name, ext = os.path.splitext(file)

                        # Check if the file has a final version
                        final_version = f"{base_name}_final{ext}"
                        if final_version in files:
                            file_to_offer = final_version
                        else:
                            file_to_offer = file

                        # Store the file paths for download
                        file_dict[file_to_offer] = os.path.join(root, file_to_offer)

            if file_dict:
                st.success("Select a file from the dropdown menu to download!")
                # Create a dropdown menu for file selection
                selected_file = st.selectbox("Select a file to download", options=list(file_dict.keys()))

                if selected_file:
                    file_path = file_dict[selected_file]
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label=f"Download {selected_file}",
                            data=f,
                            file_name=selected_file
                        )

                    # Upload button to re-upload the downloaded file
                    uploaded_file = st.file_uploader("Re-upload the downloaded file (CSV or PDF)", type=["csv", "pdf", "txt"], key="tab6_file_uploader")
                    if uploaded_file:
                        new_file_path = os.path.join("processed", f"{uploaded_file.name}")
                        with open(new_file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        st.success(f"File {uploaded_file.name} has been re-uploaded and saved as {new_file_path}")
            else:
                st.warning("No files found for the specified company.")
        else:
            st.error("Please specify the company name in the first tab.")

def login():
    st.markdown("<h1 style='color:white;'>Login</h1>", unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in st.session_state['user_data']['usernames']:
            index = st.session_state['user_data']['usernames'].index(username)
            if bcrypt.checkpw(password.encode(), st.session_state['user_data']['passwords'][index]):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.experimental_rerun()  # Rerun the app after login
            else:
                st.error("Incorrect password")
        else:
            st.error("Username not found")

if __name__ == "__main__":
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if not st.session_state['logged_in']:
        add_user()
        login()
    else:
        main()
import streamlit as st
from openai import OpenAI
import os
import shutil
import PyPDF2
import pandas as pd
import json
import numpy as np
from zipfile import ZipFile
import requests
import bcrypt
import base64
from styles_and_html import get_page_bg_and_logo_styles

api_key = st.secrets["general"]["OPENAI_API_KEY"]
if not api_key:
    st.error("API key not found. Please set the OPENAI_API_KEY environment variable.")
    st.stop()

client = OpenAI(api_key=api_key)

# Function to read PDF content
def read_pdf(file_path):
    content = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page_num in range(len(reader.pages)):
            content += reader.pages[page_num].extract_text()
    return content

# Function to run a GPT task
def run_gpt_task(instructions, prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": prompt}
        ],
        max_tokens=4000
    )
    return response.choices[0].message.content

# Load instructions from JSON file
with open('instructions.json', 'r') as f:
    instructions = json.load(f)

# Load prompts from JSON file
with open('prompts.json', 'r') as f:
    prompts = json.load(f)

# Create a folder to save uploaded files if it doesn't exist
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Create a folder to save processed files if it doesn't exist
if not os.path.exists("processed"):
    os.makedirs("processed")

# Create a subfolder inside processed to store output files
output_folder = os.path.join("processed", "output_files")
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

if 'user_data' not in st.session_state:
    st.session_state['user_data'] = {'usernames': [], 'passwords': []}

def add_user():
    predefined_users = {
        "bm1961": "Charlotte-182"}

    for username, password in predefined_users.items():
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        st.session_state['user_data']['usernames'].append(username)
        st.session_state['user_data']['passwords'].append(hashed_password)

# Get the styles and HTML for the background and logo
page_bg_img, logo_html = get_page_bg_and_logo_styles()

# Apply CSS and HTML
st.markdown(page_bg_img, unsafe_allow_html=True)
st.markdown(logo_html, unsafe_allow_html=True)

st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        background-color: white;
        border-radius: 10px;
        border: 1px solid white;
        gap: 6px;
        padding-top: 15px;
        padding-bottom: 15px;
        color: black !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: white;
        color: black !important;
    }
    .stMarkdown, .stTextInput, .stHeader, .stTitle, .stSubheader, .stCaption, .stText, .stExpander, .stDownloadButton, .stException {
        color: white !important;
        background-color: transparent !important;
        border-radius: 10px;
        padding: 10px;
    }
    .stTextInput > label, .stTextInput > div, .stTextInput > label > div {
        color: white !important;
    }
    .stButton button {
        color: black !important;
    }
    .stBox {
        border: 1px solid white;
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
        background-color: transparent;
        color: white !important;
    }
    .css-1l7r3cz, .css-1d391kg, .css-hxt7ib, .css-18e3th9, .css-1aehpv1, .css-2trqyj, .css-1v3fvcr, .css-1cpxqw2, .css-12oz5g7, .css-1v0mbdj {
        color: white !important;
        background-color: transparent !important;
        border-radius: 10px;
    }
    .css-1g6gooi {
        display: none;
    }
    .stDownloadButton > button {
        color: black !important;
        margin-top: 20px;
        display: block;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown("<h1 style='color:white;'>Document Analysis and Processing</h1>", unsafe_allow_html=True)
    # Tabs: Upload documents and specify company name, Run GPT Tasks, Upload CSV Files, Download Specific Outputs, Upload Pillar Page
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Upload Required Documents", 
        "Execute GPT Tasks", 
        "Process and Analyze CSV Files", 
        "Generate Website Content", 
        "Create Pillar Page", 
        "Download & Overwrite Files"
    ])

    with tab1:
        st.markdown("<h1 style='color:white;'>Step 1: Upload Required Documents</h1>", unsafe_allow_html=True)
        st.markdown("""
            <p>In this step, you need to upload the workshop documents for analysis.</p>
            <p>The system will save the uploaded documents for further processing in the subsequent steps as inputs for the model.</p>
        """, unsafe_allow_html=True)
        company_name = st.text_input("Specify the company name")

        required_files = [
            "product_list.pdf",
            "USP.pdf",
            "key_stats.pdf",
            "about_us.pdf",
            "colour_scheme.pdf"
        ]

        uploaded_files = {}
        for file in required_files:
            file_path = os.path.join("uploads", f"{company_name}_{file}")
            if not os.path.exists(file_path):
                uploaded_files[file] = st.file_uploader(f"Upload {file}", type="pdf")
            else:
                uploaded_files[file] = None  # File already exists

        if st.button("Upload Documents"):
            if company_name:
                all_files_uploaded = True
                for file_name, uploaded_file in uploaded_files.items():
                    if uploaded_file is not None:
                        with open(os.path.join("uploads", f"{company_name}_{file_name}"), "wb") as f:
                            f.write(uploaded_file.getbuffer())
                    elif not os.path.exists(os.path.join("uploads", f"{company_name}_{file_name}")):
                        all_files_uploaded = False
                        st.error(f"File {file_name} not found. Please upload it.")

                if all_files_uploaded:
                    st.success("Files uploaded successfully!")
                else:
                    st.error("Please upload all required documents.")
            else:
                st.error("Please specify the company name.")

        # Add download button for this tab's files
        if os.path.exists("uploads"):
            with ZipFile(os.path.join("processed", f"{company_name}_uploads.zip"), "w") as zipf:
                for file_name in required_files:
                    file_path = os.path.join("uploads", f"{company_name}_{file_name}")
                    if os.path.exists(file_path):
                        zipf.write(file_path, file_name)
            with open(os.path.join("processed", f"{company_name}_uploads.zip"), "rb") as zipf:
                st.download_button(
                    label="Download Uploaded Documents",
                    data=zipf,
                    file_name=f"{company_name}_uploads.zip"
                )

    with tab2:
        st.markdown("<h1 style='color:white;'>Step 2: Execute GPT Tasks</h1>", unsafe_allow_html=True)
        st.markdown("""
            <p>In this step, you will run GPT tasks to process the uploaded documents. </p>
            <p>Outcome: The system will then generate outputs such as buyer persona, mission statement, brand voice, SEO summaries, and keywords for further research.</p>
        """, unsafe_allow_html=True)

        if st.button("Run GPT Tasks"):
            if company_name:
                document_contents = {}
                all_files_present = True
                for file_name in required_files:
                    file_path = os.path.join("uploads", f"{company_name}_{file_name}")
                    if os.path.exists(file_path):
                        document_contents[file_name] = read_pdf(file_path)
                    else:
                        st.error(f"File {file_name} not found. Please upload it in the first tab.")
                        all_files_present = False
                        break

                if all_files_present:
                    # Separate document texts
                    product_list_text = document_contents.get("product_list.pdf", "")
                    USP_text = document_contents.get("USP.pdf", "")
                    key_stats_text = document_contents.get("key_stats.pdf", "")
                    about_us_text = document_contents.get("about_us.pdf", "")
                    colour_scheme_text = document_contents.get("colour_scheme.pdf", "")

                    # 1. Buyer Persona
                    prompt_buyer_persona = prompts["prompt_buyer_persona"].format(company_name=company_name, product_list=product_list_text, USP=USP_text, key_stats=key_stats_text, about_us=about_us_text)
                    buyer_persona = run_gpt_task(instructions["buyer_persona"], prompt_buyer_persona)
                    with open(os.path.join("processed", f"{company_name}_buyer_persona.txt"), "w") as f:
                        f.write(buyer_persona)

                    # 2. English Editor for Buyer Persona
                    prompt_english_editor = prompts["prompt_english_editor"].format(file_name=f"{company_name}_buyer_persona.txt", file_content=buyer_persona)
                    english_editor_output = run_gpt_task(instructions["english_editor"], prompt_english_editor)
                    with open(os.path.join("processed", f"{company_name}_buyer_persona.txt"), "w") as f:
                        f.write(english_editor_output)

                    # 3. Mission Statement
                    prompt_mission_statement = prompts["prompt_mission_statement"].format(company_name=company_name, product_list=product_list_text, USP=USP_text, key_stats=key_stats_text, about_us=about_us_text, buyer_persona=buyer_persona)
                    mission_values = run_gpt_task(instructions["mission_statement"], prompt_mission_statement)
                    with open(os.path.join("processed", f"{company_name}_mission_values.txt"), "w") as f:
                        f.write(mission_values)

                    # 4. English Editor for Mission Values
                    prompt_english_editor_mission = prompts["prompt_english_editor"].format(file_name=f"{company_name}_mission_values.txt", file_content=mission_values)
                    english_editor_mission_output = run_gpt_task(instructions["english_editor"], prompt_english_editor_mission)
                    with open(os.path.join("processed", f"{company_name}_mission_values.txt"), "w") as f:
                        f.write(english_editor_mission_output)

                    # 5. SEO Summarizer
                    prompt_seo_summarizer = prompts["prompt_seo_summarizer"].format(product_list=product_list_text, USP=USP_text, key_stats=key_stats_text, about_us=about_us_text, buyer_persona=buyer_persona)
                    seo_summarizer_output = run_gpt_task(instructions["seo_summarizer"], prompt_seo_summarizer)
                    with open(os.path.join("processed", f"{company_name}_seo_summarizer.txt"), "w") as f:
                        f.write(seo_summarizer_output)

                    # 6. English Editor for SEO Summarizer
                    prompt_english_editor_seo = prompts["prompt_english_editor"].format(file_name=f"{company_name}_seo_summarizer.txt", file_content=seo_summarizer_output)
                    english_editor_seo_output = run_gpt_task(instructions["english_editor"], prompt_english_editor_seo)
                    with open(os.path.join("processed", f"{company_name}_seo_summarizer.txt"), "w") as f:
                        f.write(english_editor_seo_output)

                    # 7. SEO Keywords
                    prompt_magic_words = prompts["prompt_magic_words"].format(english_editor_seo_output=english_editor_seo_output)
                    seo_keywords = run_gpt_task(instructions["magic_words"], prompt_magic_words)
                    with open(os.path.join("processed", f"{company_name}_seo_keywords.txt"), "w") as f:
                        f.write(seo_keywords)
                     # Brand Voice   
                    prompt_brand_voice = prompts["prompt_brand_voice"].format(company_name=company_name, product_list=product_list_text, USP=USP_text, key_stats=key_stats_text, about_us=about_us_text, buyer_persona=buyer_persona, mission_values=mission_values)
                    brand_voice = run_gpt_task(instructions["brand_voice"], prompt_brand_voice)
                    with open(os.path.join("processed", f"{company_name}_brand_voice.txt"), "w") as f:
                        f.write(brand_voice)
    
                    prompt_english_editor_brand = prompts["prompt_english_editor"].format(file_name=f"{company_name}_brand_voice.txt", file_content=brand_voice)
                    english_editor_brand_output = run_gpt_task(instructions["english_editor"], prompt_english_editor_brand)
                    with open(os.path.join("processed", f"{company_name}_brand_voice.txt"), "w") as f:
                        f.write(english_editor_brand_output)

                    # Zip the specific output files for download
                    with ZipFile(os.path.join("processed", f"{company_name}_specific_outputs_gpt_tasks.zip"), "w") as zipf:
                        zipf.write(os.path.join("processed", f"{company_name}_buyer_persona.txt"), f"{company_name}_buyer_persona.txt")
                        zipf.write(os.path.join("processed", f"{company_name}_mission_values.txt"), f"{company_name}_mission_values.txt")
                        zipf.write(os.path.join("processed", f"{company_name}_seo_summarizer.txt"), f"{company_name}_seo_summarizer.txt")
                        zipf.write(os.path.join("processed", f"{company_name}_seo_keywords.txt"), f"{company_name}_seo_keywords.txt")
                        zipf.write(os.path.join("processed", f"{company_name}_brand_voice.txt"), f"{company_name}_brand_voice.txt")

                    st.success("GPT tasks have been executed and files are zipped!")

        # Add download button for this tab's files
        if os.path.exists("processed"):
            with ZipFile(os.path.join("processed", f"{company_name}_gpt_tasks.zip"), "w") as zipf:
                for file in ["buyer_persona.txt", "mission_values.txt", "seo_summarizer.txt", "seo_keywords.txt"]:
                    file_path = os.path.join("processed", f"{company_name}_{file}")
                    if os.path.exists(file_path):
                        zipf.write(file_path, file)
            with open(os.path.join("processed", f"{company_name}_gpt_tasks.zip"), "rb") as zipf:
                st.download_button(
                    label="Download GPT Task Outputs",
                    data=zipf,
                    file_name=f"{company_name}_gpt_tasks.zip"
                )

    with tab3:
        st.markdown("<h1 style='color:white;'>Step 3: Process and Analyze CSV Files</h1>", unsafe_allow_html=True)
        st.markdown("""
            <p>In this step, you need to upload CSV files for processing and analysis. The system will analyze the CSV files and generate a list of top 150 keywords based on various criteria.</p>
            <p>Outcome: The system will process the CSV files and generate a file containing the top 150 keywords.</p>
        """, unsafe_allow_html=True)

        csv_files = st.file_uploader("Upload CSV files", type="csv", accept_multiple_files=True)

        if csv_files and st.button("Process CSV Files"):
            if company_name:
                csv_file_paths = []
                for i, file in enumerate(csv_files):
                    file_path = os.path.join("uploads", f"{company_name}_csv_file_{i + 1}.csv")
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                    csv_file_paths.append(file_path)

                if csv_file_paths:
                    # Load the CSV files
                    dataframes = []
                    for i, file_path in enumerate(csv_file_paths):
                        df = pd.read_csv(file_path)
                        df['Source'] = f'{company_name}_csv_file_{i + 1}'  # Add source column with company name
                        dataframes.append(df)

                    # Concatenate the dataframes
                    combined_df = pd.concat(dataframes, ignore_index=True)

                    # Data cleaning
                    combined_df['Volume'] = pd.to_numeric(combined_df['Volume'], errors='coerce').fillna(0)
                    combined_df['Keyword Difficulty'] = pd.to_numeric(combined_df['Keyword Difficulty'], errors='coerce').fillna(100)
                    combined_df['CPC (GBP)'] = pd.to_numeric(combined_df['CPC (GBP)'], errors='coerce').fillna(0)

                    # Filter and score
                    combined_df = combined_df[(combined_df['Volume'] >= 20) | 
                                            (combined_df['CPC (GBP)'] >= 0.35) | 
                                            ((combined_df['Keyword Difficulty'] <= 50) & 
                                            (combined_df['Keyword Difficulty'] >= 10)) | 
                                            (combined_df['Keyword Difficulty'].isna())]
                    combined_df['Score'] = np.log(combined_df['Volume']) / combined_df['CPC (GBP)']

                    # Select top 150 keywords
                    top_keywords_list = []
                    remaining_slots = 150
                    for source, group in combined_df.groupby('Source'):
                        group_top = group.nlargest(15, 'Score')
                        top_keywords_list.append(group_top)
                        remaining_slots -= len(group_top)
                        if remaining_slots <= 0:
                            break

                    if remaining_slots > 0:
                        remaining_keywords = combined_df[~combined_df.index.isin(pd.concat(top_keywords_list).index)]
                        additional_keywords = remaining_keywords.nlargest(remaining_slots, 'Score')
                        top_keywords_list.append(additional_keywords)

                    top_keywords = pd.concat(top_keywords_list).nlargest(150, 'Score')['Keyword']

                    # Save the top keywords
                    output_file = os.path.join("processed", f"{company_name}_top_150_keywords.csv")
                    top_keywords.to_csv(output_file, index=False)

                    st.success("CSV files processed and top 150 keywords saved!")
                    # with open(output_file, "rb") as f:
                    #     st.download_button("Download Top 150 Keywords", f, file_name=f"{company_name}_top_150_keywords.csv")
                else:
                    st.error("No CSV files found.")
            else:
                st.error("Please specify the company name in the first tab.")

        # Add download button for this tab's files
        if os.path.exists("processed"):
            with ZipFile(os.path.join("processed", f"{company_name}_csv_analysis.zip"), "w") as zipf:
                file_path = os.path.join("processed", f"{company_name}_top_150_keywords.csv")
                if os.path.exists(file_path):
                    zipf.write(file_path, "top_150_keywords.csv")
            with open(os.path.join("processed", f"{company_name}_csv_analysis.zip"), "rb") as zipf:
                st.download_button(
                    label="Download CSV Analysis Outputs",
                    data=zipf,
                    file_name=f"{company_name}_csv_analysis.zip"
                )

    with tab4:
        st.markdown("<h1 style='color:white;'>Step 4: Generate Website Content</h1>", unsafe_allow_html=True)
        st.markdown("""
            <p>In this step, you will generate topic clusters, website structure, and web page content based on uploaded documents and processed data.</p>
        """, unsafe_allow_html=True)

        if st.button("Generate Website Content"):
            if company_name:
                document_contents = {}
                for file_name in required_files:
                    file_path = os.path.join("uploads", f"{company_name}_{file_name}")
                    if os.path.exists(file_path):
                        document_contents[file_name] = read_pdf(file_path)

                product_list_text = document_contents.get("product_list.pdf", "")
                USP_text = document_contents.get("USP.pdf", "")
                key_stats_text = document_contents.get("key_stats.pdf", "")
                about_us_text = document_contents.get("about_us.pdf", "")
                colour_scheme_text = document_contents.get("colour_scheme.pdf", "")
                colour_scheme_text = document_contents.get("brand_voice.pdf", "")

                with open(os.path.join("processed", f"{company_name}_buyer_persona.txt"), "r") as f:
                    buyer_persona = f.read()
                with open(os.path.join("processed", f"{company_name}_top_150_keywords.csv"), "r") as f:
                    top_keywords = f.read()
                with open(os.path.join("processed", f"{company_name}_mission_values.txt"), "r") as f:
                    mission_values = f.read()

                # 1. Topic Cluster Analysis
                prompt_topic_cluster = prompts["prompt_topic_cluster"].format(company_name=company_name, product_list=product_list_text,  buyer_persona=buyer_persona, seo_keywords=top_keywords)
                topic_cluster_document = run_gpt_task(instructions["topic_cluster"], prompt_topic_cluster)
                with open(os.path.join("processed", f"{company_name}_topic_cluster_document.txt"), "w") as f:
                    f.write(topic_cluster_document)

                prompt_extract_keywords = prompts["prompt_extract_keywords"].format(topic_cluster_document=topic_cluster_document)
                keywords = run_gpt_task(instructions["editor"], prompt_extract_keywords)
                with open(os.path.join("processed", f"{company_name}_keywords.txt"), "w") as f:
                    f.write(keywords)

                prompt_website_structure = prompts["prompt_website_structure"].format(company_name=company_name, product_list=product_list_text, USP=USP_text, key_stats=key_stats_text, about_us=about_us_text, buyer_persona=buyer_persona, topic_cluster_document=topic_cluster_document, keywords=keywords)
                website_structure_document = run_gpt_task(instructions["website_structure"], prompt_website_structure)
                with open(os.path.join("processed", f"{company_name}_website_structure_document.txt"), "w") as f:
                    f.write(website_structure_document)

                prompt_extract_home_page = prompts["prompt_extract_home_page"].format(website_structure_document=website_structure_document)
                home_page_structure = run_gpt_task(instructions["editor"], prompt_extract_home_page)

                with open(os.path.join("processed", f"{company_name}_brand_voice.txt"), "r") as f:
                    brand_voice_text = f.read()
                with open(os.path.join("processed", f"{company_name}_keywords.txt"), "r") as f:
                    keywords = f.read()

                prompt_home_page = prompts["prompt_home_page"].format(company_name=company_name, product_list=product_list_text, USP=USP_text, key_stats=key_stats_text, about_us=about_us_text, brand_voice_text=brand_voice_text, keywords=keywords)
                home_page_document = run_gpt_task(instructions["home_page"], prompt_home_page)
                with open(os.path.join("processed", f"{company_name}_home_page.txt"), "w") as f:
                    f.write(home_page_document)

                prompt_english_editor_home = prompts["prompt_english_editor"].format(file_name=f"{company_name}_home_page.txt", file_content=home_page_document)
                home_page_final = run_gpt_task(instructions["english_editor"], prompt_english_editor_home)
                with open(os.path.join("processed", f"{company_name}_home_page_final.txt"), "w") as f:
                    f.write(home_page_final)

                prompt_extract_about_us = prompts["prompt_extract_about_us"].format(website_structure_document=website_structure_document)
                about_us_structure = run_gpt_task(instructions["editor"], prompt_extract_about_us)

                prompt_about_us = prompts["prompt_about_us"].format(company_name=company_name, product_list=product_list_text, USP=USP_text, key_stats=key_stats_text, about_us=about_us_text,  brand_voice_text=brand_voice_text, keywords=keywords)
                about_us_document = run_gpt_task(instructions["about_us"], prompt_about_us)
                with open(os.path.join("processed", f"{company_name}_about_us.txt"), "w") as f:
                    f.write(about_us_document)

                prompt_english_editor_about_us = prompts["prompt_english_editor"].format(file_name=f"{company_name}_about_us.txt", file_content=about_us_document)
                about_us_final = run_gpt_task(instructions["english_editor"], prompt_english_editor_about_us)
                with open(os.path.join("processed", f"{company_name}_about_us_final.txt"), "w") as f:
                    f.write(about_us_final)

                # Zip the specific outputs for download
                with ZipFile(os.path.join("processed", f"{company_name}_specific_outputs_website_content.zip"), "w") as zipf:
                    zipf.write(os.path.join("processed", f"{company_name}_topic_cluster_document.txt"), f"{company_name}_topic_cluster_document.txt")
                    zipf.write(os.path.join("processed", f"{company_name}_keywords.txt"), f"{company_name}_keywords.txt")
                    zipf.write(os.path.join("processed", f"{company_name}_website_structure_document.txt"), f"{company_name}_website_structure_document.txt")
                    zipf.write(os.path.join("processed", f"{company_name}_home_page.txt"), f"{company_name}_home_page.txt")
                    zipf.write(os.path.join("processed", f"{company_name}_home_page_final.txt"), f"{company_name}_home_page_final.txt")
                    zipf.write(os.path.join("processed", f"{company_name}_about_us.txt"), f"{company_name}_about_us.txt")
                    zipf.write(os.path.join("processed", f"{company_name}_about_us_final.txt"), f"{company_name}_about_us_final.txt")

                st.success("Website content has been generated and zipped!")

        # Add download button for this tab's files
        if os.path.exists("processed"):
            with ZipFile(os.path.join("processed", f"{company_name}_website_content.zip"), "w") as zipf:
                for file in ["topic_cluster_document.txt", "keywords.txt", "website_structure_document.txt", "brand_voice.txt", "home_page.txt", "home_page_final.txt", "about_us.txt", "about_us_final.txt"]:
                    file_path = os.path.join("processed", f"{company_name}_{file}")
                    if os.path.exists(file_path):
                        zipf.write(file_path, file)
            with open(os.path.join("processed", f"{company_name}_website_content.zip"), "rb") as zipf:
                st.download_button(
                    label="Download Website Content Outputs",
                    data=zipf,
                    file_name=f"{company_name}_website_content.zip"
                )

    with tab5:
        st.markdown("<h1 style='color:white;'>Step 5: Create Pillar Page</h1>", unsafe_allow_html=True)
        st.markdown("""
            <p>In this step, you will enter the content or upload a Pillar Page PDF document.</p>
            <p>Outcome: The system will generate and edit the content of the pillar page based on the provided text or document.</p>
        """, unsafe_allow_html=True)

        # Text input for prompt
        pillar_page_text = st.text_area("Enter the content for the Pillar Page")

        # Option to upload a PDF as before
        pillar_page_file = st.file_uploader("Or upload a Pillar Page PDF", type="pdf")

        # Process the entered text or uploaded PDF
        if pillar_page_file:
            pillar_page_path = os.path.join("uploads", f"{company_name}_pillar_page.pdf")
            with open(pillar_page_path, "wb") as f:
                f.write(pillar_page_file.getbuffer())

            pillar_page_content = read_pdf(pillar_page_path)
        else:
            pillar_page_content = pillar_page_text

        if st.button("Process Pillar Page"):
            if company_name:
                # Read content from the saved PDFs
                document_contents = {}
                for file_name in required_files:
                    file_path = os.path.join("uploads", f"{company_name}_{file_name}")
                    if os.path.exists(file_path):
                        document_contents[file_name] = read_pdf(file_path)

                # Separate document texts
                product_list_text = document_contents.get("product_list.pdf", "")
                USP_text = document_contents.get("USP.pdf", "")
                key_stats_text = document_contents.get("key_stats.pdf", "")
                about_us_text = document_contents.get("about_us.pdf", "")
                colour_scheme_text = document_contents.get("colour_scheme.pdf", "")

                # Read the existing files
                with open(os.path.join("processed", f"{company_name}_buyer_persona.txt"), "r") as f:
                    buyer_persona = f.read()
                with open(os.path.join("processed", f"{company_name}_top_150_keywords.csv"), "r") as f:
                    top_keywords = f.read()
                with open(os.path.join("processed", f"{company_name}_mission_values.txt"), "r") as f:
                    mission_values = f.read()
                with open(os.path.join("processed",f"{company_name}_brand_voice.txt"), "r") as f:
                    brand_voice = f.read()
                with open(os.path.join("processed", f"{company_name}_keywords.txt"), "r") as f:
                    keywords = f.read()

                # Ensure pillar_page_content is read only if pillar_page_file was uploaded
                if pillar_page_file:
                    pillar_page_content = read_pdf(pillar_page_path)

                # Generate the prompt for the pillar page
                prompt_pillar_page = prompts["prompt_pillar_page"].format(
                    company_name=company_name, 
                    pillar_page_content=pillar_page_content, 
                    product_list=product_list_text, 
                    USP=USP_text, 
                    key_stats=key_stats_text, 
                    about_us=about_us_text, 
                    brand_voice_text=brand_voice, 
                    keywords=keywords
                )
                pillar_page_document = run_gpt_task(instructions["pillar_page"], prompt_pillar_page)
                with open(os.path.join("processed", f"{company_name}_pillar_page.txt"), "w") as f:
                    f.write(pillar_page_document)

                # English Editor for Pillar Page
                prompt_english_editor_pillar = prompts["prompt_english_editor"].format(file_name=f"{company_name}_pillar_page.txt", file_content=pillar_page_document)
                pillar_page_final = run_gpt_task(instructions["english_editor"], prompt_english_editor_pillar)
                with open(os.path.join("processed", f"{company_name}_pillar_page_final.txt"), "w") as f:
                    f.write(pillar_page_final)

                # Zip the pillar page files for download
                with ZipFile(os.path.join("processed", f"{company_name}_specific_outputs_pillar_page.zip"), "w") as zipf:
                    zipf.write(os.path.join("processed", f"{company_name}_pillar_page.txt"), f"{company_name}_pillar_page.txt")
                    zipf.write(os.path.join("processed", f"{company_name}_pillar_page_final.txt"), f"{company_name}_pillar_page_final.txt")

                st.success("Pillar page has been processed and edited!")

        # Add download button for this tab's files
        if os.path.exists("processed"):
            with ZipFile(os.path.join("processed", f"{company_name}_pillar_page.zip"), "w") as zipf:
                for file in ["pillar_page.txt", "pillar_page_final.txt"]:
                    file_path = os.path.join("processed", f"{company_name}_{file}")
                    if os.path.exists(file_path):
                        zipf.write(file_path, file)
            with open(os.path.join("processed", f"{company_name}_pillar_page.zip"), "rb") as zipf:
                st.download_button(
                    label="Download Pillar Page Outputs",
                    data=zipf,
                    file_name=f"{company_name}_pillar_page.zip"
                )

    with tab6:
        st.markdown("<h1 style='color:white;'>Step 6: Download & Overwrite Files</h1>", unsafe_allow_html=True)
        st.markdown("""
            <p>In this step, you can download and re-upload processed files for further editing.</p>
            <p>Outcome: The system allows you to download the generated files and re-upload any edited versions.</p>
        """, unsafe_allow_html=True)

        if company_name:
            file_dict = {}

            # Scan the 'processed' folder for files
            for root, dirs, files in os.walk("processed"):
                for file in files:
                    if company_name in file:
                        file_path = os.path.join(root, file)
                        base_name, ext = os.path.splitext(file)

                        # Check if the file has a final version
                        final_version = f"{base_name}_final{ext}"
                        if final_version in files:
                            file_to_offer = final_version
                        else:
                            file_to_offer = file

                        # Store the file paths for download
                        file_dict[file_to_offer] = os.path.join(root, file_to_offer)

            if file_dict:
                st.success("Select a file from the dropdown menu to download!")
                # Create a dropdown menu for file selection
                selected_file = st.selectbox("Select a file to download", options=list(file_dict.keys()))

                if selected_file:
                    file_path = file_dict[selected_file]
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label=f"Download {selected_file}",
                            data=f,
                            file_name=selected_file
                        )

                    # Upload button to re-upload the downloaded file
                    uploaded_file = st.file_uploader("Re-upload the downloaded file (CSV or PDF)", type=["csv", "pdf", "txt"], key="tab6_file_uploader")
                    if uploaded_file:
                        new_file_path = os.path.join("processed", f"{uploaded_file.name}")
                        with open(new_file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        st.success(f"File {uploaded_file.name} has been re-uploaded and saved as {new_file_path}")
            else:
                st.warning("No files found for the specified company.")
        else:
            st.error("Please specify the company name in the first tab.")

def login():
    st.markdown("<h1 style='color:white;'>Login</h1>", unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in st.session_state['user_data']['usernames']:
            index = st.session_state['user_data']['usernames'].index(username)
            if bcrypt.checkpw(password.encode(), st.session_state['user_data']['passwords'][index]):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.experimental_rerun()  # Rerun the app after login
            else:
                st.error("Incorrect password")
        else:
            st.error("Username not found")

if __name__ == "__main__":
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if not st.session_state['logged_in']:
        add_user()
        login()
    else:
        main()

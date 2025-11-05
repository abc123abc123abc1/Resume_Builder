import os
import streamlit as st
from pathlib import Path
import json
import base64
from dotenv import load_dotenv

from models.schema import ResumeData, ProfileData, Education, EmploymentHistory
from services.pdf_generator import PDFGenerator
from services.resume_matcher import ResumeMatcher

# Set page config
st.set_page_config(
    page_title="AI Resume Builder",
    page_icon="📄",
    layout="wide"
)

# Load environment variables from .env file if it exists
load_dotenv()

# Profile management functions
def get_profiles_directory():
    """Get the profiles directory path and create it if it doesn't exist."""
    current_dir = Path(__file__).parent
    profiles_dir = current_dir / "profiles"
    if not profiles_dir.exists():
        profiles_dir.mkdir(exist_ok=True)
    return profiles_dir

def save_profile(profile_data):
    """Save a profile to a JSON file."""
    profiles_dir = get_profiles_directory()
    profile_path = profiles_dir / f"{profile_data.name.replace(' ', '_')}.json"
    
    with open(profile_path, 'w') as f:
        f.write(profile_data.model_dump_json(indent=2))
    
    return profile_path

def load_profile(profile_name):
    """Load a profile from a JSON file."""
    profiles_dir = get_profiles_directory()
    profile_path = profiles_dir / f"{profile_name}.json"
    
    if not profile_path.exists():
        return None
    
    with open(profile_path, 'r') as f:
        profile_data = json.load(f)
    
    return ProfileData(**profile_data)

def delete_profile(profile_name):
    """Delete a profile JSON file."""
    profiles_dir = get_profiles_directory()
    profile_path = profiles_dir / f"{profile_name}.json"
    
    if profile_path.exists():
        profile_path.unlink()  # Delete the file
        return True
    return False  # Return False for failure case

def get_available_profiles():
    """Get a list of available profile names."""
    profiles_dir = get_profiles_directory()
    profiles = []
    
    for profile_file in profiles_dir.glob("*.json"):
        profiles.append(profile_file.stem.replace('_', ' '))
    
    return profiles  # Return the list of profiles

# Initialize services
@st.cache_resource
def load_services():
    current_dir = Path(__file__).parent
    template_path = current_dir / "templates" / "resume_template.docx"
    credentials_path = current_dir / "pdfservices-api-credentials.json"
    
    # Check if template exists
    if not template_path.exists():
        st.error(f"Template file not found: {template_path}")
        st.stop()
    
    # Create profiles directory if it doesn't exist
    profiles_dir = current_dir / "profiles"
    profiles_dir.mkdir(exist_ok=True)
    
    # Set environment variables for Adobe PDF Services if credentials file exists
    pdf_gen = None
    if credentials_path.exists():
        try:
            # Load credentials from JSON file
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                
            # Set environment variables based on the nested structure in the credentials file
            if 'client_credentials' in creds:
                os.environ['PDF_SERVICES_CLIENT_ID'] = creds['client_credentials'].get('client_id', '')
                os.environ['PDF_SERVICES_CLIENT_SECRET'] = creds['client_credentials'].get('client_secret', '')
                
                # Add organization ID if needed
                if 'service_principal_credentials' in creds and 'organization_id' in creds['service_principal_credentials']:
                    os.environ['PDF_SERVICES_ORGANIZATION_ID'] = creds['service_principal_credentials'].get('organization_id', '')
                    
                pdf_gen = PDFGenerator(str(credentials_path))
            else:
                st.warning("Invalid credentials file format. Missing 'client_credentials' section.")
        except Exception as e:
            st.warning(f"Error loading Adobe API credentials: {str(e)}")
            st.info("Using mock PDF generator for demo purposes.")
    else:
        st.warning(f"Adobe API credentials file not found: {credentials_path}")
        st.info("Using mock PDF generator for demo purposes.")
    
    # Check for OpenAI API key
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    if not openai_api_key:
        st.warning("OpenAI API key not found. Using legacy resume generation method.")
        st.info("Set the OPENAI_API_KEY environment variable for enhanced resume generation.")
    
    return {
        "template_path": str(template_path),
        "pdf_generator": pdf_gen
    }

services = load_services()

# Helper function to create download links
def get_download_link(content, filename, text):
    b64 = base64.b64encode(content).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{text}</a>'
    return href

# App UI
st.title("🚀 AI Resume Builder")
st.markdown("""
This app automatically tailors your resume based on a job description. 
It analyzes the job requirements and creates a personalized resume that 
highlights your most relevant experience.
""")

# Create tabs for the main app sections - reversed order
resume_tab, profile_tab = st.tabs(["Resume Generator", "Profile Management"])

# Resume Generator Tab (now first)
with resume_tab:
    st.header("Resume Generator")
    
    # Profile selection and job description inputs
    available_profiles = get_available_profiles()
    
    if not available_profiles:
        st.warning("No profiles found. Please create a profile first in the Profile Management tab.")
        st.info("Switch to the 'Profile Management' tab above to create your first profile.")
    else:
        # Select profile
        profile_name = st.selectbox("Select your profile", available_profiles)
        selected_profile = None
        
        if profile_name:
            selected_profile = load_profile(profile_name.replace(' ', '_'))
            if selected_profile:
                # Show selected profile info
                st.success(f"Using profile: {selected_profile.name}")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Name:** {selected_profile.name}")
                    st.markdown(f"**Email:** {selected_profile.email}")
                with col2:
                    st.markdown(f"**Location:** {selected_profile.location}")
        
        # Target Job Title input (optional)
        st.subheader("Target Job Title (Optional)")
        target_job_title = st.text_input(
            "Enter the job title you're applying for",
            placeholder="e.g., Generative AI Engineer, Senior ML Engineer",
            help="If provided, this title will be used in your resume instead of your original title. Leave blank to use your profile title."
        )
        
        # Original Resume input
        st.subheader("Your Original Resume/Experience")
        original_resume = st.text_area(
            "Paste your original resume or experience details here", 
            height=250,
            help="Paste your current resume, CV, or detailed work experience. This will be used as the base for generating your tailored resume."
        )
        
        # Job description input
        st.subheader("Job Description")
        job_description = st.text_area(
            "Paste the job description here", 
            height=200,
            help="Copy and paste the entire job description to get the best results."
        )
        
        # Generate button
        if st.button("Generate Tailored Resume", type="primary", 
                    disabled=not all([selected_profile, job_description, original_resume])):
            with st.spinner("Analyzing job description and tailoring your resume..."):
                # Prepare user info from the selected profile
                # Use target job title if provided, otherwise use profile title
                resume_title = target_job_title.strip() if target_job_title and target_job_title.strip() else selected_profile.title
                
                user_info = {
                    "name": selected_profile.name,
                    "title": resume_title,
                    "email": selected_profile.email,
                    "phone": selected_profile.phone,
                    "location": selected_profile.location,
                    "linkedin": selected_profile.linkedin if hasattr(selected_profile, "linkedin") else None,
                    "education": [edu.model_dump() for edu in selected_profile.education] if selected_profile.education else [],
                    "employment_history": [job.model_dump() for job in selected_profile.employment_history] if hasattr(selected_profile, "employment_history") and selected_profile.employment_history else []
                }
                
                # Create a new ResumeMatcher instance with user-provided resume text
                resume_matcher = ResumeMatcher(experience_text=original_resume)
                
                print("----- Generating tailored resume -----")
                resume_data = resume_matcher.generate_tailored_resume(job_description, user_info)
                print("----- Tailored resume generated -----")

                # Generate files if PDF generator is available
                if services["pdf_generator"]:
                    try:
                        files = services["pdf_generator"].generate_resume(
                            resume_data, 
                            services["template_path"]
                        )
                        
                        # Create download buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(
                                get_download_link(files["docx"], f"{user_info['name'].replace(' ', '_')}_resume.docx", "Download DOCX"),
                                unsafe_allow_html=True
                            )
                        with col2:
                            st.markdown(
                                get_download_link(files["pdf"], f"{user_info['name'].replace(' ', '_')}_resume.pdf", "Download PDF"),
                                unsafe_allow_html=True
                            )
                    except Exception as e:
                        st.error(f"Error generating resume files: {str(e)}")
                else:
                    st.info("Adobe PDF Services credentials not found. Download functionality disabled in demo mode.")
                    
                    # Save resume data as JSON for demo
                    json_data = resume_data.model_dump_json(indent=2)
                    st.download_button(
                        label="Download Resume Data (JSON)",
                        data=json_data,
                        file_name=f"{user_info['name'].replace(' ', '_')}_resume_data.json",
                        mime="application/json"
                    )

# Profile Management Tab (now second)
with profile_tab:
    st.header("Profile Management")
    profiles_subtab, new_profile_subtab = st.tabs(["View Profiles", "Create New Profile"])

    # View Profiles sub-tab
    with profiles_subtab:
        available_profiles = get_available_profiles()
        
        if available_profiles:
            profile_name = st.selectbox("Select a profile to view", available_profiles, key="view_profile_select")
            if profile_name:
                selected_profile = load_profile(profile_name.replace(' ', '_'))
                if selected_profile:
                    st.success(f"Profile for {selected_profile.name}")
                    
                    # Display profile details
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Name:** {selected_profile.name}")
                        st.markdown(f"**Email:** {selected_profile.email}")
                    with col2:
                        st.markdown(f"**Location:** {selected_profile.location}")
                        if selected_profile.linkedin:
                            st.markdown(f"**LinkedIn:** [{selected_profile.linkedin}]({selected_profile.linkedin})")
                    
                    # Display employment history if available
                    if hasattr(selected_profile, 'employment_history') and selected_profile.employment_history:
                        st.subheader("Employment History")
                        for job in selected_profile.employment_history:
                            st.markdown(f"**{job.company_name}** - {job.period}")
                            st.markdown(f"{job.location}")
                    
                    # Display education if available
                    if selected_profile.education:
                        st.subheader("Education")
                        for edu in selected_profile.education:
                            st.markdown(f"**{edu.university_name}** - {edu.period}")
                            st.markdown(f"{edu.degree}, {edu.location}")
                    
                    # Add delete button
                    if st.button("Delete Profile", type="primary", key="delete_profile"):
                        with st.spinner("Deleting profile..."):
                            if delete_profile(profile_name.replace(' ', '_')):
                                st.success(f"Profile '{profile_name}' has been deleted!")
                                st.info("Please refresh the page to see the updated profile list.")
                            else:
                                st.error("Error deleting profile.")
        else:
            st.info("No profiles found. Create a new profile to get started.")

    # Create New Profile sub-tab
    with new_profile_subtab:
        with st.form("profile_form"):
            st.subheader("Personal Information")
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name")
                location = st.text_input("Location (City, State)")
            with col2:
                email = st.text_input("Email Address")
                linkedin = st.text_input("LinkedIn Profile URL", help="e.g., https://www.linkedin.com/in/username")
            
            # Employment History section
            st.subheader("Employment History")
            
            # Create containers for employment entries
            employment_entries = []
            
            # Use session state to track number of employment entries
            if 'num_employment_entries' not in st.session_state:
                st.session_state.num_employment_entries = 1
            
            # Generate employment entry fields based on session state
            for i in range(1, st.session_state.num_employment_entries + 1):
                st.markdown(f"**Employment #{i}**")
                company_name = st.text_input("Company Name", key=f"company{i}")
                col1, col2 = st.columns(2)
                with col1:
                    job_period = st.text_input("Period (e.g., 01/2021 - 05/2025)", key=f"job_period{i}")
                with col2:
                    job_location = st.text_input("Location (e.g., Chicago, IL)", key=f"job_location{i}")
                
                if all([company_name, job_period, job_location]):
                    employment_entries.append(
                        EmploymentHistory(
                            company_name=company_name,
                            period=job_period,
                            location=job_location
                        )
                    )
                
                # Add a separator between entries
                if i < st.session_state.num_employment_entries:
                    st.markdown("---")
            
            # Add more employment entries button (outside the form submit button)
            if st.session_state.num_employment_entries < 3:
                add_job_col1, add_job_col2 = st.columns([1, 3])
                with add_job_col1:
                    if st.form_submit_button("Add Another Employment", type="secondary"):
                        st.session_state.num_employment_entries += 1
                        st.rerun()
            
            # Education section
            st.subheader("Education")
            
            # Create containers for education entries
            education_entries = []
            
            # Use session state to track number of education entries
            if 'num_education_entries' not in st.session_state:
                st.session_state.num_education_entries = 1
            
            # Generate education entry fields based on session state
            for i in range(1, st.session_state.num_education_entries + 1):
                st.markdown(f"**Education #{i}**")
                university = st.text_input("University Name", key=f"university{i}")
                col1, col2 = st.columns(2)
                with col1:
                    period = st.text_input("Period (e.g., 2018-2022)", key=f"period{i}")
                    location_edu = st.text_input("Location", key=f"location_edu{i}")
                with col2:
                    degree = st.text_input("Degree", key=f"degree{i}")
                
                if all([university, period, location_edu, degree]):
                    education_entries.append(
                        Education(
                            university_name=university,
                            period=period,
                            location=location_edu,
                            degree=degree
                        )
                    )
                
                # Add a separator between entries
                if i < st.session_state.num_education_entries:
                    st.markdown("---")
            
            # Add more education entries button
            if st.session_state.num_education_entries < 2:
                add_edu_col1, add_edu_col2 = st.columns([1, 3])
                with add_edu_col1:
                    if st.form_submit_button("Add Another Education", type="secondary"):
                        st.session_state.num_education_entries += 1
                        st.rerun()
            
            # Save profile button
            submit_button = st.form_submit_button("Save Profile")
            
            if submit_button:
                if all([name, email, location]):
                    # Create profile data
                    profile_data = ProfileData(
                        name=name,
                        email=email,
                        location=location,
                        linkedin=linkedin if linkedin else None,
                        education=education_entries,
                        employment_history=employment_entries
                    )
                    
                    # Save profile
                    profile_path = save_profile(profile_data)
                    st.success(f"Profile saved successfully to {profile_path}")
                else:
                    st.error("Please fill in all required fields.")

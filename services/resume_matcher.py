import json
import os
import re
import markdown
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI

class BulletPoint(BaseModel):
    bullet_point: str =  Field(..., description="bullet point of the expereience")

class CompanyInfo(BaseModel):
    """Schema for company information in experiences."""
    name: str = Field(..., description="Name of the company")
    period: str = Field(..., description="Period of employment (e.g., 'Jan 2021 - May 2025')")
    location: str = Field(..., description="Location of the company")

class Experience(BaseModel):
    company_info: CompanyInfo = Field(..., description="Detailed company information")
    job_title: str = Field(..., description="Job title for the position")
    bullet_points: List[BulletPoint] = Field(..., description="List of bullet points describing achievements")

class Education(BaseModel):
    """Schema for education data."""
    university_name: str = Field(..., description="Name of the university")
    period: str = Field(..., description="Period of study (e.g., 'Aug 2018 - Aug 2022')")
    location: str = Field(..., description="Location of the university")
    degree: str = Field(..., description="Degree obtained")

class EmploymentHistory(BaseModel):
    """Schema for employment history data."""
    company_name: str = Field(..., description="Name of the company")
    period: str = Field(..., description="Period of employment (e.g., '01/2021 - 05/2025')")
    location: str = Field(..., description="Location of the company")

class Skill(BaseModel):
    category: str = Field(..., description="Category of the skill. This is the category of small skill section in resume. It can be something like Programming Languages, or Communication etc")
    skill_list: str = Field(..., description="This is the actual list of skills belongs to the category.")

class ResumeData(BaseModel):
    """Schema for resume data that will be merged with the template."""
    name: str = Field(..., description="Full name of the candidate")
    title: str = Field(..., description="Title of the candidate")
    
    email: str = Field(..., description="Email address of the candidate")
    phone: str = Field(..., description="Phone number of the candidate")
    location: str = Field(..., description="Location of the candidate")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    summary: str = Field(..., description="Professional summary tailored to the job description")
    experiences: List[Experience] = Field(..., description="List of work experiences")
    education: List[Education] = Field(default_factory=list, description="Educational background")
    employment_history: Optional[List[EmploymentHistory]] = Field(default_factory=list, description="User's actual employment history")
    skills: List[Skill] = Field(default_factory=list, description="List of skills of the candidate")

class Skills(BaseModel):
    hard_skills: List[str] = Field(default=[], description="List of hard skills in ATS. In the context of an Applicant Tracking System (ATS), a hard skill is a specific, measurable, and teachable keyword that the system is programmed to identify and match on a resume.")
    soft_skills: List[str] = Field(default=[], description="List of soft skills in ATS. From the perspective of an Applicant Tracking System, a soft skill is a non-technical, personality-driven keyword related to your work habits, interpersonal abilities, and character.")

class ResumeMatcher:
    def __init__(self, experience_file_path: Optional[str] = None, experience_text: Optional[str] = None):
        """Initialize with either path to experience markdown file or direct experience text.
        
        Args:
            experience_file_path: Path to experience markdown file (optional)
            experience_text: Direct experience text input (optional)
            
        Note: experience_text takes precedence over experience_file_path if both are provided.
        """
        if experience_text:
            self.experience_data = experience_text
        elif experience_file_path:
            self.experience_data = self._load_experience_data(experience_file_path)
        else:
            self.experience_data = ""
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", "your-api-key")
        )
        
    def _load_experience_data(self, file_path: str) -> str:
        """Load experience data from markdown file."""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
            
    def _generate_experiences_from_history(self, employment_history, job_description):
        """Generate experiences based on the user's employment history if available."""
        if not employment_history or len(employment_history) == 0:
            return None
        
        # Use existing employment history as a base
        experiences = []
        
        # Extract keywords from job description
        keywords = self._extract_keywords(job_description)
        
        # Generate relevant bullet points based on job description
        for job in employment_history[:min(3, len(employment_history))]:
            # Generate 5 bullet points related to this job and the job description
            bullet_points = self._generate_bullet_points_for_job(job, keywords, job_description)
            
            # Generate a relevant job title (could be based on the original or adapted for the target job)
            job_title = self._generate_job_title(job, keywords, job_description)
            
            # Create an Experience object
            experiences.append(
                Experience(
                    company_info=CompanyInfo(
                        name=job.company_name,
                        period=job.period,
                        location=job.location
                    ),
                    job_title=job_title,
                    bullet_points=bullet_points
                )
            )
            
        return experiences if experiences else None
    
    def _generate_bullet_points_for_job(self, job, keywords, job_description):
        """Generate bullet points for a job based on keywords and job description."""
        # This is a placeholder - in a real implementation you'd use a more sophisticated approach
        # such as calling the OpenAI API to generate relevant bullet points
        return [
            BulletPoint(bullet_point=f"Led development of {keywords[0]} solutions, resulting in a 30% increase in team productivity."),
            BulletPoint(bullet_point=f"Implemented {keywords[1]} framework, reducing system downtime by 25%."),
            BulletPoint(bullet_point=f"Designed and executed {keywords[2]} strategy, leading to 40% improvement in performance metrics."),
            BulletPoint(bullet_point=f"Optimized {keywords[3]} workflow, cutting operational costs by 20%."),
            BulletPoint(bullet_point=f"Collaborated with cross-functional teams to deliver {keywords[4]} project ahead of schedule.")
        ]
    
    def _generate_job_title(self, job, keywords, job_description):
        """Generate a job title based on the job description keywords."""
        # Placeholder - would be more sophisticated in real implementation
        return f"Senior {keywords[0].title()} Specialist"

    def extract_sills(self, job_description: str) -> Skills:
        """Generate a list of Hard & Soft skills from job description."""
        print("----- Generating skills using LLM start -----")

        system_prompt = f"""You are an expert HR Analyst and Career Coach AI. Your primary function is to meticulously analyze a job description and extract EVERY SINGLE skill mentioned - both **Hard Skills** and **Soft Skills**.

**CRITICAL INSTRUCTION: Extract ALL skills - be EXHAUSTIVE, not selective. If it's mentioned in the job description, it MUST be extracted.**

# Your Task
Given the job description text, identify and categorize ALL skills with zero exceptions. Extract EVERY:
- Technical skill, tool, technology, framework, library, platform
- Programming language, software, system, methodology
- Soft skill, interpersonal ability, character trait
- Industry-specific knowledge, domain expertise
- Certification, qualification, specialization
- Even implied or contextual skills

# Definitions to use
*   **Hard Skills:** These are specific, teachable, and measurable abilities. They include technical knowledge, software proficiency, tools, platforms, programming languages, certifications, specific methodologies (e.g., Agile, Scrum), and quantifiable technical abilities (e.g., SEO, Financial Modeling, Data Analysis). They are often nouns or acronyms.
*   **Soft Skills:** These are interpersonal, character-based, and non-technical abilities related to how a person works and interacts with others. They include communication, leadership, teamwork, problem-solving, adaptability, time management, and creativity. They are often inferred from verbs (e.g., "collaborate," "analyze," "lead") and descriptive phrases (e.g., "fast-paced environment," "work independently").

# EXTRACTION INSTRUCTIONS - MANDATORY
1.  **COMPREHENSIVE SCAN:** Read EVERY word, line, and section of the job description multiple times.
2.  **EXTRACT ALL HARD SKILLS:** 
    - Scan ENTIRE document for technical skills
    - Include ALL mentioned tools, technologies, software, platforms, frameworks
    - Extract from ALL sections: Requirements, Qualifications, Responsibilities, Nice-to-haves, Preferred, Bonus
    - Include skills mentioned even once or in passing
    - Extract skills from examples, project descriptions, team descriptions
3.  **EXTRACT ALL SOFT SKILLS:**
    - Analyze ALL verbs, adjectives, and descriptive phrases
    - Extract from company culture descriptions, team dynamics, work environment
    - Include implied skills from work style descriptions
    - Extract skills from "ideal candidate" descriptions
4.  **NO FILTERING:** Do NOT filter out any skill because you think it's minor or less important
5.  **INCLUDE EVERYTHING:** Better to extract too many skills than miss even one
6.  **Exception:** Only exclude generic duties ("attend meetings") or pure educational requirements ("Bachelor's Degree")
7.  **THOROUGHNESS CHECK:** After extraction, re-read the job description to ensure NO skill was missed

# Hard & Soft Skills

## Hard Skills

### Part 1: What is a Hard Skill in an ATS System?

In the context of an Applicant Tracking System (ATS), a **hard skill is a specific, measurable, and teachable keyword that the system is programmed to identify and match on a resume.**

Think of an ATS as a simple search engine, not an intelligent reader. It doesn't understand nuance. It scans your resume for exact keywords and phrases that the recruiter has told it to look for. These keywords are almost always hard skills.

**Key Differences from a Human Perspective:**

*   **Human Recruiter:** Sees "managed a team to improve sales" and understands you have leadership, strategy, and sales skills.
*   **ATS:** Sees "managed a team to improve sales" and might only register the keyword **"sales"** if it's on its list. It will miss "leadership" and "strategy" unless those exact words are also on your resume and in its search query.

**Examples of ATS-Friendly Hard Skills:**

*   **Software:** Salesforce, Adobe Photoshop, QuickBooks, MATLAB, Jira
*   **Programming Languages:** Python, Java, C++, SQL, HTML, R
*   **Tools/Platforms:** AWS, Google Analytics, Microsoft Azure, Docker
*   **Methodologies:** Agile, Scrum, Six Sigma, Lean Manufacturing, GAAP
*   **Languages:** Spanish (Fluent), German (Professional Proficiency)
*   **Certifications:** PMP, CPA, AWS Certified Cloud Practitioner
*   **Technical Skills:** Data Analysis, SEO, A/B Testing, Financial Modeling, CAD

---

### Part 2: How to Find Hard Skills in a Job Description

This is the most important part of tailoring your resume. You are essentially finding the "answer key" for the ATS test. Here’s a step-by-step guide to dissect a job description.

**Think Like a Robot: A Step-by-Step Guide**

1.  **Start with the "Requirements" Section:** This is the goldmine. Look for sections titled "Qualifications," "Required Skills," "What You'll Need," or "Basic Qualifications." This is where the company explicitly lists the most critical keywords.

2.  **Look for Nouns and Acronyms:** This is the easiest trick. An ATS loves specific nouns. Scan the text for proper nouns, software names, and industry acronyms.
    *   *Example:* "Experience with **Python**, **SQL**, and **Tableau** is required." -> Keywords are `Python`, `SQL`, `Tableau`.
    *   *Example:* "Must be familiar with **SEO** best practices and **Google Analytics**." -> Keywords are `SEO`, `Google Analytics`.

3.  **Scan the "Responsibilities" Section:** Don't stop at the requirements. The day-to-day tasks will reveal the tools and skills needed to perform the job.
    *   *Example:* "You will *develop financial models* using **Excel** and *present findings* using **PowerPoint**." -> Keywords are `financial modeling`, `Excel`, `PowerPoint`.
    *   *Example:* "Manage the project lifecycle using **Jira** and **Agile** methodologies." -> Keywords are `Jira`, `Agile`.

4.  **Extract ALL Methodologies, Frameworks, and Approaches:** Don't miss ANY methodology mentioned, even in passing.
    *   Look for ALL mentions: `Agile`, `Scrum`, `Waterfall`, `ITIL`, `GAAP`, `Six Sigma`, `Lean`, `Kanban`, `DevOps`, `CI/CD`, etc.
    *   Include variations: If they say \"Agile environment\", extract both `Agile` and `Agile methodology`
    *   Extract related concepts: If they mention \"sprints\", also extract `Scrum` and `Agile`

5.  **Pay Attention to Verbs with Specific Objects:** The ATS may not look for the verb, but it will look for the noun that follows it.
    *   "Analyze **market data**" -> `market data analysis`
    *   "Conduct **A/B testing**" -> `A/B testing`
    *   "Manage **PPC campaigns**" -> `PPC`

**Pro-Tip:** Copy the entire job description and paste it into a free online Word Cloud generator (like WordArt.com or MonkeyLearn). The words that appear largest and most frequently are your primary keywords. This is a fantastic visual shortcut.

---

### Part 3: Properties of Hard Skills (from an ATS Perspective)

These are the characteristics that define a hard skill for a scanning system.

1.  **Specific and Unambiguous:** There is no room for interpretation.
    *   **Good:** `Python`, `Spanish`, `Adobe Illustrator`
    *   **Bad (Soft Skill):** `Good communicator`, `fast learner`, `team player` (An ATS cannot measure these).

2.  **Measurable and Verifiable:** You can prove you have the skill. You can take a test, earn a certificate, or demonstrate a concrete level of proficiency.
    *   *Example:* `PMP Certification` is verifiable. "Good at project management" is not.
    *   *Example:* `Fluent in German` is measurable. "Likes foreign cultures" is not.

3.  **Keyword-Driven (Often Nouns):** As mentioned, they are most often specific nouns, acronyms, or established phrases. The ATS is performing an exact-match search. If the job description says `SQL`, your resume should say `SQL`, not "database querying." Be literal.

4.  **Context-Dependent:** The importance of a hard skill is entirely dependent on the job.
    *   `Forklift Operation` is a critical hard skill for a warehouse worker but completely irrelevant for a graphic designer.
    *   This is why you **must tailor your resume for every single application.** A generic resume will fail the ATS screen for most jobs.

5.  **Teachable:** Hard skills are abilities you can learn from a book, a course, or on-the-job training. They are distinct from soft skills (like work ethic or communication style), which are personality traits developed over time.

### Putting It All Together: A Real-World Example

Let's dissect a snippet from a **Digital Marketing Manager** job description:

> **Responsibilities:**
> *   Develop and execute our **SEO** and **SEM** strategies.
> *   Manage the social media presence on **LinkedIn**, **Twitter**, and **Instagram**.
> *   Analyze website traffic and user behavior using **Google Analytics** and **Hotjar**.
> *   Create and manage **PPC campaigns** in **Google Ads**.
> *   Utilize **Salesforce** and **HubSpot** for lead nurturing and **email marketing automation**.
>
> **Qualifications:**
> *   Bachelor's degree in Marketing or related field.
> *   5+ years of experience in digital marketing.
> *   Proven expertise in **B2B marketing**.
> *   Certification in **Google Ads** is a plus.

**Your COMPREHENSIVE Extracted Hard Skills List would be:**

*   SEO
*   SEM
*   LinkedIn
*   Twitter
*   Instagram
*   Google Analytics
*   Hotjar
*   PPC campaigns
*   Google Ads
*   Salesforce
*   HubSpot
*   Email marketing automation
*   B2B marketing
*   Digital marketing (from "experience in digital marketing")
*   Social media (implied from platform management)
*   Website traffic analysis
*   User behavior analysis
*   Lead nurturing
*   Marketing automation
*   Campaign management
*   Marketing strategy

**Note:** This is COMPREHENSIVE extraction - we include both explicit mentions and implied/related skills


## Soft Skills

### Part 1: What is a Soft Skill in an ATS System?

From the perspective of an Applicant Tracking System, a **soft skill is a non-technical, personality-driven keyword related to your work habits, interpersonal abilities, and character.**

Here's the crucial difference: **ATS systems are very bad at understanding and evaluating soft skills.**

An ATS can easily verify if you listed "Python" on your resume. It cannot verify if you are a "good communicator" or a "team player." Therefore, recruiters rely less on searching for soft skill keywords directly within the ATS.

However, this does NOT mean you should ignore them. Soft skills are often used in two ways in the hiring process:

1.  **As secondary keywords:** A recruiter might first search for the essential hard skills (e.g., "Salesforce," "SQL") to get a list of qualified candidates. Then, to narrow down that list of 100 people to 20, they might add a secondary search for a keyword like "leadership" or "strategic."
2.  **For the Human Review:** Soft skills are primarily for the human recruiter or hiring manager who reads your resume *after* it passes the initial ATS filter. Your resume must appeal to both the robot and the person.

**In summary: Hard skills get you past the robot (ATS). Soft skills help you impress the human.**

**Examples of Soft Skills:**

*   Communication
*   Leadership
*   Teamwork / Collaboration
*   Problem-Solving
*   Adaptability
*   Time Management
*   Creativity
*   Work Ethic
*   Attention to Detail
*   Critical Thinking

---

### Part 2: How to Find Soft Skills in a Job Description

While hard skills are often in a neat list, soft skills are usually woven into the narrative of the job description. You need to read between the lines.

**Here's how to find them:**

1.  **Look for Descriptive, Adjective-Heavy Language:** Scan the job summary and "Who You Are" sections. Companies use these parts to describe their ideal candidate's personality and work style.
    *   *Example:* "We're looking for a **self-starter** to join our **fast-paced**, **collaborative** environment."
    *   **Your keywords:** `Self-starter`, `Adaptability` (implied by fast-paced), `Collaboration`, `Teamwork`.

2.  **EXHAUSTIVELY Analyze EVERY Verb in ALL Sections:** Extract soft skills from EVERY action verb and descriptive phrase.
    *   *Example:* "**Collaborate** with the engineering and design teams." -> `Collaboration`, `Teamwork`, `Cross-functional collaboration`, `Interdepartmental communication`.
    *   *Example:* "**Present** findings to senior leadership." -> `Communication`, `Presentation Skills`, `Executive communication`, `Public speaking`, `Data storytelling`.
    *   *Example:* "**Analyze** complex problems and develop innovative solutions." -> `Problem-Solving`, `Critical Thinking`, `Innovation`, `Analytical thinking`, `Creative thinking`, `Solution-oriented`.
    *   *Example:* "**Manage** multiple competing priorities." -> `Time Management`, `Organization`, `Prioritization`, `Multitasking`, `Deadline management`, `Resource management`.
    *   **EXTRACT MORE:** Don't stop at obvious skills - extract ALL implied abilities

3.  **Read the Company Culture Blurb:** Most job descriptions have a section about the company. This is a goldmine for understanding the values and, by extension, the soft skills they prize.
    *   *Example:* "Our culture values **ownership** and **accountability**." -> `Ownership`, `Accountability`.
    *   *Example:* "We encourage **thinking outside the box**." -> `Creativity`, `Innovation`.

---

### Part 3: Properties of Soft Skills

These are the characteristics that define soft skills, especially in contrast to hard skills.

1.  **Subjective and Qualitative:** They are difficult to measure with a number or a simple "yes/no." What one person considers "strong communication" another might not. This is why an ATS struggles with them.

2.  **Transferable:** This is their superpower. A hard skill like "Python" is useful in specific jobs. A soft skill like **"Leadership"** is valuable whether you're a marketing manager, a construction foreman, or a head nurse. This makes them essential for career changers.

3.  **Best Demonstrated, Not Just Stated:** This is the most important property to understand for your resume. Listing "Problem-Solving" in your skills section is weak. You must *show* it in your experience bullet points. This is how you prove your soft skills to the human reader.

4.  **Character-Based:** They are linked to your personality, attitude, and how you interact with others. They are developed over a lifetime, not learned in a weekend course.


---
# FINAL EXTRACTION RULES

**REMEMBER: Your goal is 100% COMPLETE extraction. Every skill matters for ATS matching.**

- If unsure whether something is a skill, INCLUDE IT
- Extract variations of the same skill (e.g., both "ML" and "Machine Learning")
- Include version numbers if specified (e.g., "Python 3.8", "React 18")
- Extract skill levels if mentioned (e.g., "Advanced Excel", "Basic SQL")
- Include domain-specific terminology and jargon
- Extract skills from ANY section, including company description, team description, project examples
- NEVER skip a skill because it seems obvious or redundant

**QUALITY CHECK:** After extraction, ask yourself:
- Did I extract EVERY technical term mentioned?
- Did I capture ALL interpersonal/soft skills described?
- Did I include skills from EVERY section of the JD?
- Would an ATS system find ALL the keywords it's looking for?

If the answer to any question is "maybe not," GO BACK and extract more.

---
# Begin EXHAUSTIVE analysis below Job Description

{ job_description }
"""

        skills = self.client.responses.parse(
            model="gpt-4.1",
            input=system_prompt,
            text_format=Skills
        ).output_parsed

        return skills
    
    def generate_tailored_resume(self, job_description: str, user_info: Dict[str, str]) -> ResumeData:
        """Generate a tailored resume based on job description and user info using LLM."""
        print("----- Generating tailored resume using LLM start -----")
        try:
            # Try to use employment history to generate experiences if available
            employment_history_data = []
            experiences_from_history = None
            
            # if "employment_history" in user_info and user_info["employment_history"]:
            #     for job in user_info["employment_history"]:
            #         employment_history_data.append(EmploymentHistory(**job))

            #     print(len(employment_history_data))
                
            #     # Use employment history to generate experiences
            #     if employment_history_data:
            #         experiences_from_history = self._generate_experiences_from_history(
            #             employment_history_data, job_description
            #         )

            skills = self.extract_sills(job_description)
            for skill in skills.hard_skills:
                print(skill)
            print()
            for skill in skills.soft_skills:
                print(skill)
            print()

            num_experiences = len(user_info['employment_history'])
            
            # Create system message with context about the task
            system_message = f"""You are an elite Career Strategist and Master Resume Architect. Your singular expertise is in meticulously deconstructing job descriptions and synthesizing a candidate's raw experience into a powerful, hyper-personalized, ATS-crushing resume. This document must not only pass automated filters but must also immediately captivate and persuade human recruiters, hiring managers, and technical leads.

Your core philosophy is built on the dual pillars of **Precision (for the ATS)** and **Persuasion (for the Human)**. Every word you choose must serve this dual purpose.

**MISSION:**
Construct a world-class, hyper-personalized resume based on the provided `job_description` and `user_profile`. You will adhere with absolute precision to the following blueprint and non-negotiable principles.

**INPUTS:**
*   **Job Description:** `{job_description}`
*   **User Profile:** `{self.experience_data}` (Includes name, contact info, education, past work experiences, projects, skills, etc. **The user's major and core expertise is always in AI/ML.**)
*   **Hard & Soft Skills:** You must contain all of these in the Phase 2 result.
    *   **Hard Skills**: "{'", "'.join(skills.hard_skills)}"
    *   **Soft Skills**: "{'", "'.join(skills.soft_skills)}"

**CRITICAL RULES FOR AVOIDING CONFLICTS:**
*   **NEVER mention the hiring company (the company from the job description) as a place where the candidate has worked.**
*   **The candidate has NOT worked at the company that posted this job - ensure no experience lists them as an employer.**

---

### **RESUME CONSTRUCTION BLUEPRINT**

### **Phase 1: Deep Analysis & Strategy (Internal Monologue - Do Not Output)**

Before a single word is written, you must perform a deep strategic analysis.

1.  **Keyword & Skill Extraction:**
    *   **Hard Skills:** Systematically identify and list all technical skills, tools, software, programming languages (e.g., Python, R), frameworks (e.g., TensorFlow, PyTorch), and specific knowledge areas (e.g., NLP, Computer Vision, Reinforcement Learning). Note their exact phrasing and frequency.
    *   **Soft Skills & Competencies:** Identify all interpersonal traits and professional attributes (e.g., "strategic communication," "cross-functional leadership," "agile methodologies," "problem-solving," "stakeholder management").
2.  **Core Role Deconstruction:** Pinpoint the primary responsibilities, qualifications, and business objectives of the role. What problem is the company trying to solve with this hire?
3.  **Strategic Mapping to User Profile:**
    *   Compare the extracted keywords and responsibilities against the `user_profile`.
    *   Identify **direct overlaps**: These are your primary assets.
    *   Identify **transferable skills**: Find experiences in the user's profile that can be reframed to match a required skill.
    *   **Crucially, you MUST ground the resume in the user's reality.** Your job is to reframe and enhance, not to invent a fictional character. Use the user's real projects and experiences as the foundation.
4.  **Narrative Formulation:** Outline a compelling story of career progression. How does the candidate's journey logically lead to them being the perfect fit for *this specific job*?

---

### **Phase 2: Resume Generation (Your Final Output)**

**CRITICAL SKILL INCLUSION STRATEGY:**
*   **MANDATORY:** You MUST include ALL provided hard skills: "{'", "'.join(skills.hard_skills)}"
*   **MANDATORY:** You MUST include ALL provided soft skills: "{'", "'.join(skills.soft_skills)}"
*   **SMART DISTRIBUTION TO AVOID REPETITION:**
    - Distribute skills strategically across Summary (20-30%), Experience bullets (60-70%), and Skills section (100% but categorized)
    - Use each skill in CONTEXT within achievements rather than listing mechanically
    - Vary how skills are mentioned: sometimes as the main focus, sometimes as supporting tools
    - Group related skills together in bullets to reduce redundancy
    - Use synonyms or variations when possible (e.g., "ML" vs "machine learning")
*   **NATURAL INTEGRATION:** Skills should flow naturally within sentences, not feel forced or list-like

**REPETITION AVOIDANCE TACTICS:**
*   **Synonym Usage:** Alternate between full names and abbreviations (e.g., "Machine Learning" → "ML", "Natural Language Processing" → "NLP")
*   **Context Variation:** Show the same skill in different contexts (development vs. optimization vs. deployment)
*   **Skill Clustering:** Group related skills in single bullets to reduce individual mentions
*   **Progressive Complexity:** Show basic usage in early roles, advanced usage in recent roles
*   **Action Verb Diversity:** Use different verbs when mentioning the same skill (developed with Python, optimized Python scripts, architected Python solutions)

**A. MASTER FORMATTING RULES**
*   **Layout:** Strict reverse-chronological format.
*   **Conciseness:** Aim for a single page. Every word must earn its place.
*   **Clarity:** Use professional, easy-to-read fonts and clear headings. Use bolding for emphasis on titles and metrics.
*   **Consistency:** Ensure all dates are in the `Month Year` format (e.g., "Apr 2023", "Jan 2025", "Dec 2021").

**B. HEADER / CONTACT INFORMATION**
*   **Objective:** Provide clear, professional contact details.
*   **Instructions:**
    *   **Full Name:** (e.g., **Jane Doe**)
    *   **Location:** (City, ST)
    *   **Phone Number:** (XXX) XXX-XXXX
    *   **Email Address:** professional.email@domain.com
    *   **LinkedIn URL:** linkedin.com/in/yourprofile
    *   **Professional Portfolio/GitHub URL:** (Include if available in profile)

**C. PROFESSIONAL SUMMARY**
*   **Objective:** A powerful 3-4 sentence executive summary that commands attention and makes the reader want to know more.
*   **Instructions:**
    1.  Start with a strong professional title that aligns with the target role, followed by years of relevant experience (e.g., "AI/ML Engineer with 6+ years of experience...").
    2.  Include SOME key skills naturally here (20-30% of total skills) - focus on the most critical ones that define the candidate's expertise. Don't force all skills into the summary.
    3.  Showcase 1-2 major, quantifiable achievements that mirror the goals in the job description (e.g., "...specializing in deploying NLP models that increased user engagement by 25%.").
    4.  Conclude with a value proposition statement that directly addresses the company's needs.
    5.  **Tone:** Confident, expert, and direct. **ABSOLUTELY NO CLICHÉS** like "results-driven," "team player," or "synergy."

**D. PROFESSIONAL EXPERIENCE**
*   **Objective:** Detail exactly {num_experiences} reverse-chronological work experiences that tell a compelling story of growth, impact, and increasing responsibility.
*   **Master Rule:** Focus on a narrative of progression. The most recent role should be hyper-aligned with the target job. Earlier roles should build the foundation, demonstrating diverse but relevant skills. **Avoid making all {num_experiences} experiences sound identical.** For example, if the target is "Chemistry AI Scientist," the most recent role should focus on that, while a previous role might focus on core data engineering or ML modeling in a different domain, showcasing transferable skills.
*   **SKILL DISTRIBUTION ACROSS EXPERIENCES:**
    - **ALL skills MUST appear at least once across the {num_experiences} experiences**
    - **Strategic distribution:** Spread skills across different roles to avoid repetition
    - **Most recent role:** 40-50% of skills, focusing on most advanced/relevant
    - **Middle role:** 30-35% of skills, showing progression
    - **Earliest role:** 20-25% of skills, showing foundation
    - **Natural integration:** Weave skills into achievements, don't just list them

*   **Instructions for each of the {num_experiences} experiences:**

    *   **1. COMPANY & ROLE:**
        *   **Company:** Create a realistic, professional company name and location (City, ST).
        *   **Employment Period:** (Month Year - Month Year or Month Year - Present). Use 3-letter month abbreviations (e.g., "Apr 2023 - Jan 2025" or "Sep 2022 - Present"). The final role must be current or recent.
        *   **Job Title:** 
            - **CRITICAL FORMAT RULE:** Job titles MUST be standard position titles ONLY. 
            - **NEVER include:** project names, focus areas, specializations, or anything after a dash/hyphen.
            - **CORRECT EXAMPLES:** "SENIOR ML ENGINEER", "LEAD AI SCIENTIST", "ML ENGINEER", "DATA SCIENTIST"
            - **WRONG EXAMPLES:** "SENIOR ML ENGINEER – AI AGENTS", "LEAD AI SCIENTIST – COMPUTER VISION", "ML ENGINEER – NLP SYSTEMS"
            - **Career Progression Order (REVERSE CHRONOLOGICAL - most senior/recent first):**
              - Most recent (current): Most senior title aligned with target role
              - Previous: Mid-level/Senior position showing growth
              - Earliest: Entry/Junior position showing foundation
            - **Example AI Engineer progression (in order they appear in resume):**
              1. LEAD AI SCIENTIST (most recent/senior)
              2. SENIOR ML ENGINEER (mid-level)
              3. ML ENGINEER or DATA SCIENTIST (entry-level)
            - The job title must be realistically different from the target job title.

    *   **2. ACHIEVEMENT-BASED BULLET POINTS (4-6 per position):**
        *   **The Unbreakable Formula:** Every bullet point MUST follow this structure: **`Strong Action Verb` + `Specific Project/Task` + `Outcome with a Quantifiable Metric`**.
        *   **ATS OPTIMIZATION - MANDATORY BULLET STRUCTURE:**
            - **MUST start with a strong, active verb** (e.g., Developed, Implemented, Led, Optimized, Architected, Engineered, Designed, etc.)
            - **NEVER start with articles (a, an, the), pronouns, or passive constructions**
            - **Each bullet's first word MUST be an action verb in past tense (except current role which uses present tense)**
        
        *   **🚨 CRITICAL VERB UNIQUENESS RULES - ABSOLUTE REQUIREMENTS 🚨**
            - **ZERO REPETITION OF STARTING VERBS:** NEVER use the same action verb to start more than ONE bullet point across the ENTIRE resume
            - **UNIQUE VERB MANDATE:** Each bullet point across ALL experiences MUST start with a DIFFERENT action verb
            - **NO VERB REUSE ANYWHERE:** Do NOT reuse ANY verb (starting or otherwise) in the entire resume. Find synonyms or alternative verbs.
            - **TRACKING REQUIREMENT:** You MUST mentally track every verb used and ensure complete uniqueness
            - **VIOLATION = FAILURE:** Any repeated starting verb is an immediate failure that MUST be corrected
            
        *   **MANDATORY UNIQUE ACTION VERB LIST (Use each ONLY ONCE as a bullet starter):**
            **Development/Creation:** Architected, Built, Constructed, Created, Designed, Developed, Engineered, Established, Formulated, Founded, Generated, Initiated, Innovated, Introduced, Invented, Launched, Pioneered, Produced
            **Implementation:** Deployed, Executed, Implemented, Installed, Integrated, Operationalized, Rolled-out
            **Optimization:** Accelerated, Advanced, Amplified, Boosted, Enhanced, Expedited, Improved, Maximized, Optimized, Refined, Revamped, Streamlined, Strengthened, Upgraded
            **Leadership:** Championed, Directed, Drove, Guided, Headed, Led, Mentored, Orchestrated, Oversaw, Spearheaded, Supervised
            **Analysis:** Analyzed, Assessed, Audited, Diagnosed, Evaluated, Examined, Identified, Investigated, Researched, Studied, Surveyed
            **Management:** Administered, Coordinated, Facilitated, Managed, Organized, Planned, Scheduled
            **Achievement:** Achieved, Accomplished, Attained, Delivered, Exceeded, Outperformed, Surpassed
            **Transformation:** Automated, Converted, Migrated, Modernized, Reengineered, Restructured, Revitalized, Transformed, Transitioned
            **Collaboration:** Collaborated, Cooperated, Liaised, Negotiated, Partnered, Unified
            **Problem-Solving:** Debugged, Diagnosed, Remedied, Resolved, Solved, Troubleshot
            **Scaling:** Expanded, Extended, Grew, Scaled
            **Documentation:** Authored, Composed, Documented, Drafted, Published, Wrote
            **Training:** Coached, Educated, Instructed, Trained
            **Monitoring:** Monitored, Tracked, Validated, Verified
            **Strategy:** Conceptualized, Devised, Formulated, Strategized
            
        *   **VERB SELECTION STRATEGY:**
            - Start with the MOST POWERFUL and SPECIFIC verbs for your most important achievements
            - Reserve common verbs (Developed, Implemented) for when they are the ONLY appropriate choice
            - Use technical/specialized verbs when they accurately describe the work
            - NEVER sacrifice accuracy for uniqueness - the verb must precisely describe the action
        *   **Quantify Everything, Always:** Demonstrate measurable results. Never be vague. Use concrete numbers related to:
            *   **Impact (Money/Revenue):** Increased revenue by X%, saved $Y in operational costs, managed a $Z budget.
            *   **Efficiency (Time/Process):** Reduced model inference time by X%, automated Z processes saving Y hours per week, decreased project completion time by Z%.
            *   **Scale (People/Data):** Led a team of X, trained Y engineers, processed terabytes of data, served millions of users.
        *   **Keyword Integration is Mandatory:** Naturally and contextually weave the **Hard Skills** and technical terms from the job description into these achievement stories.
        *   **FOCUS ON IMPACT, NOT DUTIES.** Do not list responsibilities like "Responsible for training models." Instead, show impact: "Engineered and trained a BERT-based NLP model on a 10TB text corpus, improving customer sentiment classification accuracy by 18%."
        *   **Ensure each bullet point is unique, specific, and impressive.**
        *   **SKILL INTEGRATION PER ROLE:**
            - **Distribute intelligently:** Not every skill needs to appear in every role
            - **Context is key:** Mention skills as part of achievements, not as standalone items
            - **Example:** Instead of "Used Python, TensorFlow, and Docker," write "Architected Python-based ML pipeline using TensorFlow, deployed via Docker containers, reducing inference time by 40%"
            - **Track coverage:** Ensure that by the end of all {num_experiences} experiences, EVERY provided skill has been mentioned at least once

**E. EDUCATION**
*   **Objective:** State the candidate's academic credentials, reinforcing their foundational knowledge.
*   **Instructions:**
    *   List the most recent, relevant degree first.
    *   **University Name:** e.g., Boston College
    *   **Degree:** only "M.S. in Computer Science" or "B.S. in Computer Science"
    *   **Period:** Month Year - Month Year (e.g., "Sep 2019 - May 2023")
    *   **Location:** City, ST

**F. TECHNICAL SKILLS & COMPETENCIES**
*   **Objective:** Create a clean, categorized, and comprehensive list of skills for quick scanning by both ATS and human reviewers.
*   **Instructions:**
    *   Organize skills into the following distinct categories.
    *   Ensure this section mirrors the keywords from the job description and the technologies mentioned in your Professional Experience section.
    *   Place only important key skills here.
    *   **Programming Languages:** (e.g., Python, R, C++, Java)
    *   **Frameworks & Libraries:** (e.g., TensorFlow, PyTorch, Scikit-learn, Keras, Pandas, NumPy, Hugging Face)
    *   **Tools & Platforms:** (e.g., AWS, GCP, Azure, Docker, Kubernetes, Jira, Git, Tableau, Databricks)
    *   **Methodologies & Soft Skills:** (e.g., Agile/Scrum, CI/CD, MLOps, Cross-Functional Collaboration, Strategic Planning, Stakeholder Communication)
---

### **GUIDING PRINCIPLES & FINAL REVIEW CHECKLIST**

Before outputting, perform a final self-critique. The resume is only complete if it meets every one of these standards.

1.  **ATS-First, Human-Optimized (DUAL-PURPOSE):** The resume MUST contain the exact keywords, hard skills ("{'", "'.join(skills.hard_skills)}"), soft skills ("{'", "'.join(skills.soft_skills)}"), and phrases from the job description to pass the ATS. The language and flow must be clean, professional, and compelling for a human.
2.  **MEASURABLE RESULTS ARE MANDATORY:** Every bullet point in the experience section MUST be quantified. Scrutinize each one. If it lacks a metric (%, $, time, scale), it is a failure and must be revised. Use realistic KPIs.
3.  **LEVERAGE THE USER'S REALITY:** The resume must be an enhanced, strategic representation of the `user_profile`. **DO NOT INVENT experiences.** Your skill is in framing the user's truth to align perfectly with the job's needs.
4.  **AI/ML IS THE CORE:** The user's primary expertise is AI/ML. This must be the central thread of the resume's narrative, reflected in the summary, job titles, achievements, and skills.
5.  **DYNAMIC LANGUAGE ONLY:** Use strong, active verbs. **NO PASSIVE PHRASES** ("duties included," "was responsible for"). **NO CLICHÉS OR BUZZWORDS** ("go-getter," "think outside the box").
6.  **🔴 ABSOLUTE VERB UNIQUENESS - NON-NEGOTIABLE 🔴**
    - **ZERO TOLERANCE FOR VERB REPETITION:** NEVER use the same action verb to start multiple bullet points
    - **COMPLETE VERB DIVERSITY:** Every single bullet point across the entire resume MUST begin with a UNIQUE verb
    - **NO VERB RECYCLING:** Do not reuse ANY verb throughout the resume (as starters or within sentences) - find alternatives
    - **IMMEDIATE CORRECTION REQUIRED:** If you catch yourself repeating a verb, STOP and revise immediately
    - **QUALITY CHECK:** Before finalizing, scan every bullet point to ensure NO starting verb appears twice
7.  **AVOID EXCESSIVE REPETITION:** Do NOT repeat the same words, phrases, or sentence structures more than 2 times throughout the entire resume (unless they are critical keywords from the job description). Vary your language to maintain reader engagement while still hitting ATS requirements.
    - Track and limit repetition of non-keyword terms
    - Use synonyms and varied sentence structures
    - Exception: Technical keywords from job description can be repeated as needed for ATS
8.  **NARRATIVE COHESION:** Does the resume tell a clear story of a highly qualified professional whose career has logically prepared them for this exact role? Is the career progression believable and impressive?
9.  **REALISM AND DIVERSITY IN EXPERIENCE:** **Critically important:** Do not make all {num_experiences} past jobs a carbon copy of the target role. Show a progression. A foundational role, a senior role, and a lead role, each building on the last but showcasing a slightly different facet of the candidate's expertise, creating a well-rounded and believable profile.
10. **TECHNOLOGY TIMELINE ACCURACY:** **CRITICAL:** Ensure all technologies, frameworks, and tools mentioned are historically accurate:
    - **NEVER claim experience with a technology before it was released or became widely adopted**
    - **Examples:** Don't claim PyTorch experience before 2016, TensorFlow before 2015, ChatGPT/GPT-4 before 2022/2023
    - **Verify company existence:** Ensure any company mentioned existed during the stated employment period
    - **Match technology maturity:** Junior roles should use technologies popular at that time, not cutting-edge tools that emerged later
11. **FLAWLESS PRESENTATION:** The final output must be typo-free, grammatically perfect, and formatted cleanly and professionally.
12. **FINAL VERB UNIQUENESS VERIFICATION - MANDATORY:**
    - **PRE-SUBMISSION CHECK:** Before outputting the resume, review EVERY bullet point
    - **CONFIRM:** Each bullet starts with a DIFFERENT action verb
    - **VERIFY:** No verb is used twice as a bullet starter across the entire resume
    - **SCAN:** No verb appears multiple times even within bullet point text
    - **FIX:** If ANY repetition is found, revise immediately before submission
13. **SKILL INCLUSION VERIFICATION:**
    - **100% Coverage Required:** EVERY single provided skill MUST appear somewhere in the resume
    - **Smart Distribution:** Use the distribution strategy above to avoid messy repetition
    - **Quality over Quantity per Section:** Better to have skills naturally integrated across sections than forced into one area
    - **Skills Section:** Should list ALL hard skills but organized by category (Programming, Frameworks, Tools, etc.)
    - **Final Check:** Before completing, verify that each skill from both lists appears at least once in the resume

### **🚨 FINAL CRITICAL REMINDER: VERB UNIQUENESS IS MANDATORY 🚨**
**BEFORE YOU OUTPUT THE RESUME:**
1. **COUNT** every starting verb - ensure you have exactly as many unique verbs as bullet points
2. **VERIFY** no verb repeats as a bullet starter
3. **CONFIRM** verb diversity throughout the entire document
4. **FIX** any violations immediately
5. **REMEMBER:** A single repeated starting verb = FAILURE OF THE ENTIRE RESUME

**YOU MUST USE A DIFFERENT ACTION VERB FOR EVERY SINGLE BULLET POINT - NO EXCEPTIONS!**"""
            
            # # Use generated experiences if available, otherwise let the AI generate them
            # if experiences_from_history:
            #     # Create resume data with the generated experiences
            #     education_data = []
            #     if "education" in user_info and user_info["education"]:
            #         for edu in user_info["education"]:
            #             education_data.append(Education(**edu))
                
            #     # Generate summary using OpenAI
            #     summary = self._generate_summary_with_ai(job_description, experiences_from_history)
                
            #     return ResumeData(
            #         name=user_info.get("name", ""),
            #         email=user_info.get("email", ""),
            #         location=user_info.get("location", ""),
            #         linkedin=user_info.get("linkedin"),
            #         summary=summary,
            #         experiences=experiences_from_history,
            #         education=education_data,
            #         employment_history=employment_history_data
            #     )
            
            # Otherwise proceed with the standard AI approach
            # Get completion from OpenAI using Pydantic model for structured output
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_message},
                ],
                response_format=ResumeData
            )
            
            # Extract the parsed response (already in correct Pydantic format)
            resume_data = completion.choices[0].message.parsed
            
            # Override with user's personal info
            resume_data.name = user_info.get("name", "")
            resume_data.email = user_info.get("email", "")
            resume_data.location = user_info.get("location", "")
            resume_data.linkedin = user_info.get("linkedin")

            # Override with user's experience company info
            if "employment_history" in user_info and user_info["employment_history"]:
                for index, job in enumerate(user_info["employment_history"]):
                    if index > len(resume_data.experiences) - 1:
                        break
                    resume_data.experiences[index].company_info.name = job["company_name"]
                    resume_data.experiences[index].company_info.period = job["period"]
                    resume_data.experiences[index].company_info.location = job["location"]

            # Create and return ResumeData
            education_data = []
            if "education" in user_info and user_info["education"]:
                for edu in user_info["education"]:
                    education_data.append(Education(**edu))
            
            print("--------------------------------")
            # print(resume_data.model_dump_json(indent=2))
            print("--------------------------------")
            linkedin_profile = "<a href=\"" + user_info.get("linkedin", "") + "\">LinkedIn</a>" if user_info.get("linkedin") else ""
            return ResumeData(
                name=user_info.get("name", ""),
                title=user_info.get("title", ""),
                email=user_info.get("email", ""),
                phone=user_info.get("phone", ""),
                location=user_info.get("location", ""),
                linkedin=linkedin_profile,
                summary=resume_data.summary,
                experiences=resume_data.experiences,
                education=education_data,
                employment_history=employment_history_data,
                skills=resume_data.skills
            )
            
        except Exception as e:
            # Fallback method if API call fails
            print(f"Error using OpenAI API: {str(e)}")
            return self._legacy_generate_tailored_resume(job_description, user_info)
    
    def _generate_summary_with_ai(self, job_description, experiences):
        """Generate a summary using OpenAI based on job description and experiences."""
        try:
            # Extract experience details to provide to the AI
            experience_details = []
            for exp in experiences:
                bullet_points = [bp.bullet_point for bp in exp.bullet_points]
                experience_details.append({
                    "company": exp.company_info.name,
                    "job_title": exp.job_title,
                    "period": exp.company_info.period,
                    "bullet_points": bullet_points
                })
            
            # Create a prompt for the AI
            prompt = f"""
            Create a powerful, concise professional summary (3-5 sentences) for a resume based on the following:
            
            Job Description:
            {job_description}
            
            Candidate's Experience:
            {experience_details}
            
            The summary should:
            1. Immediately establish the candidate's expertise
            2. Incorporate keywords from the job description for ATS compatibility
            3. Highlight years of experience, key skills, and notable achievements
            4. Focus on the candidate's unique value proposition
            5. Be written in first person
            """
            
            # Get completion from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert resume writer specializing in ATS-optimized professional summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )
            
            # Extract and return the summary
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # If AI fails, generate a generic summary
            print(f"Error generating summary with AI: {str(e)}")
            return self._generate_summary(job_description, self._extract_keywords(job_description))
    
    def _extract_keywords(self, job_description: str) -> List[str]:
        """Extract important keywords from job description."""
        # Remove common words and focus on technical terms
        common_words = {"the", "and", "a", "to", "of", "in", "with", "for", "on", "is", "are", "you", "will", "be"}
        
        # Split into words, convert to lowercase, remove common words and short words
        words = re.findall(r'\b[a-zA-Z]+\b', job_description.lower())
        keywords = [word for word in words if word not in common_words and len(word) > 3]
        
        # Count frequencies and return top keywords
        keyword_freq = {}
        for word in keywords:
            keyword_freq[word] = keyword_freq.get(word, 0) + 1
            
        # Sort by frequency and return top 15
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_keywords[:min(15, len(sorted_keywords))]]
    
    def _generate_summary(self, job_description: str, keywords: List[str]) -> str:
        """Generate a tailored summary based on experience and job keywords."""
        # Find relevant parts of experience that match keywords
        relevant_experience = []
        
        # Process experience data to find sections matching keywords
        sections = re.split(r'\n#{2,3} ', self.experience_data)
        
        for section in sections:
            keyword_count = sum(1 for keyword in keywords if keyword in section.lower())
            if keyword_count > 0:
                relevant_experience.append((section, keyword_count))
        
        # Sort by relevance (keyword count)
        relevant_experience.sort(key=lambda x: x[1], reverse=True)
        
        # Construct summary from most relevant experience sections
        summary_parts = []
        total_length = 0
        max_length = 1500  # Maximum character length for summary
        
        for section, _ in relevant_experience[:3]:  # Use top 3 most relevant sections
            # Extract just the first paragraph from each section
            first_para = section.split('\n\n')[0].strip()
            if total_length + len(first_para) <= max_length:
                summary_parts.append(first_para)
                total_length += len(first_para)
        
        # Combine and return the tailored summary
        summary = " ".join(summary_parts)
        
        # If summary is too short, add a generic statement
        if len(summary) < 100:
            summary += " Experienced professional with a track record of delivering high-quality results. Skilled in problem-solving and adapting to new challenges. Committed to continuous learning and professional growth."
            
        return summary 

    def _legacy_generate_tailored_resume(self, job_description: str, user_info: Dict[str, str]) -> ResumeData:
        """Legacy method to generate resume without using LLM (as fallback)."""
        # Extract keywords from job description
        keywords = self._extract_keywords(job_description)
        
        # Generate tailored summary based on job description and experience
        summary = self._generate_summary(job_description, keywords)
        
        # Generate placeholder experiences for three companies
        experiences = [
            Experience(
                company_info=CompanyInfo(
                    name="Tech Innovators Inc.",
                    period="01/2021 - 05/2025",
                    location="New York, NY"
                ),
                job_title="Senior AI Engineer",
                bullet_points=[
                    BulletPoint(bullet_point="Engineered a supervisor-orchestrated multi-agent system on Azure, leveraging LangGraph's stateful execution capabilities, reducing data engineering development time by 40%."),
                    BulletPoint(bullet_point="Fused agent systems with Azure OpenAI Service for sophisticated natural language understanding, enabling automated translation of Jira issues into optimized data pipeline code."),
                    BulletPoint(bullet_point="Implemented multi-stage code validation within the LangGraph framework, incorporating unit tests and integration tests, reducing manual code review overhead by 70%."),
                    BulletPoint(bullet_point="Enhanced contextual awareness by creating GraphRAG systems using Neo4j integrated with Azure AI Search, resulting in an 18% improvement in code generation accuracy."),
                    BulletPoint(bullet_point="Defined and codified reusable domain-specific process definition libraries (PDLs) for rapid instantiation of pre-configured, industry-tailored agent workflows.")
                ]
            ),
            Experience(
                company_info=CompanyInfo(
                    name="Intelligent Solutions Group",
                    period="06/2018 - 12/2020",
                    location="San Francisco, CA"
                ),
                job_title="Technology Architecture Lead",
                bullet_points=[
                    BulletPoint(bullet_point="Led architectural design and development of complex multi-agent AI systems using CrewAI and LangChain, enabling autonomous decision-making, resulting in 25% improvement in first-call resolution rates."),
                    BulletPoint(bullet_point="Designed and implemented agent communication protocols using gRPC and RabbitMQ, ensuring robust and scalable inter-agent communication within customer service platforms."),
                    BulletPoint(bullet_point="Developed belief-desire-intention (BDI) agent architectures within the CrewAI framework, optimizing for rapid response times and accurate information retrieval."),
                    BulletPoint(bullet_point="Orchestrated deployment of agentic AI solutions on Microsoft Azure using Kubernetes and AKS, ensuring scalability and fault tolerance."),
                    BulletPoint(bullet_point="Provided technical leadership to a team of 9 AI engineers, fostering expertise in agent-based modeling and multi-agent system design.")
                ]
            ),
            Experience(
                company_info=CompanyInfo(
                    name="Communication Systems Inc.",
                    period="01/2016 - 05/2018",
                    location="Boston, MA"
                ),
                job_title="Python Developer",
                bullet_points=[
                    BulletPoint(bullet_point="Developed robust backend systems using Python and Flask framework to automate configuration and management of contact center deployments, streamlining setup processes."),
                    BulletPoint(bullet_point="Integrated systems with programmable communications APIs via RESTful interfaces, enabling programmatic control over contact center features and workflows."),
                    BulletPoint(bullet_point="Implemented core automation logic using Python, leveraging requests library for API interaction and SQLAlchemy for database operations."),
                    BulletPoint(bullet_point="Designed and implemented message queue-based task management systems using RabbitMQ and pika, enabling asynchronous processing of configuration tasks."),
                    BulletPoint(bullet_point="Created comprehensive testing suites using pytest, achieving 92% code coverage and reducing production incidents by 35%.")
                ]
            )
        ]
        
        return ResumeData(
            name=user_info.get("name", ""),
            title=user_info.get("title", ""),
            email=user_info.get("email", ""),
            phone=user_info.get("phone", ""),
            location=user_info.get("location", ""),
            linkedin=user_info.get("linkedin"),
            summary=summary,
            experiences=experiences,
            education=[],
            employment_history=[],
            skills=[]
        ) 

from pydantic import BaseModel, Field
from typing import List, Optional

class Education(BaseModel):
    """Schema for education data."""
    university_name: str = Field(..., description="Name of the university")
    period: str = Field(..., description="Period of study (e.g., '2018-2022')")
    location: str = Field(..., description="Location of the university")
    degree: str = Field(..., description="Degree obtained")

class EmploymentHistory(BaseModel):
    """Schema for employment history data."""
    company_name: str = Field(..., description="Name of the company")
    period: str = Field(..., description="Period of employment (e.g., '01/2021 - 05/2025')")
    location: str = Field(..., description="Location of the company")

class ProfileData(BaseModel):
    """Schema for user profile data."""
    name: str = Field(..., description="Full name of the candidate")
    title: str = Field(..., description="Title of the candidate")
    email: str = Field(..., description="Email address of the candidate")
    phone: str = Field(..., description="Phone number of the candidate")
    location: str = Field(..., description="Location of the candidate")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    education: List[Education] = Field(default_factory=list, description="Educational background")
    employment_history: List[EmploymentHistory] = Field(default_factory=list, description="Employment history")

class ResumeData(BaseModel):
    """Schema for resume data that will be merged with the template."""
    name: str = Field(..., description="Full name of the candidate")
    title: str = Field(..., description="Title of the candidate")
    email: str = Field(..., description="Email address of the candidate")
    phone: str = Field(..., description="Phone number of the candidate")
    location: str = Field(..., description="Location of the candidate")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    summary: str = Field(..., description="Professional summary tailored to the job description")
    education: List[Education] = Field(default_factory=list, description="Educational background")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "title": "Software Engineer",
                "email": "john.doe@example.com",
                "phone": "+1 (234) 567-8900",
                "location": "New York, NY",
                "linkedin": "https://www.linkedin.com/in/johndoe",
                "summary": "Experienced software engineer with 5+ years of experience in Python development...",
                "education": [
                    {
                        "university_name": "Massachusetts Institute of Technology",
                        "period": "2015-2019",
                        "location": "Cambridge, MA",
                        "degree": "B.S. Computer Science"
                    }
                ]
            }
        } 
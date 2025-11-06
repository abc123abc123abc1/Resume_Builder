import os
import json
import tempfile
from pathlib import Path

# Correct imports based on the example
from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.exception.exceptions import ServiceApiException, ServiceUsageException, SdkException
from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
from adobe.pdfservices.operation.io.stream_asset import StreamAsset
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.pdfjobs.jobs.document_merge_job import DocumentMergeJob
from adobe.pdfservices.operation.pdfjobs.params.documentmerge.document_merge_params import DocumentMergeParams
from adobe.pdfservices.operation.pdfjobs.params.documentmerge.output_format import OutputFormat
from adobe.pdfservices.operation.pdfjobs.result.document_merge_result import DocumentMergePDFResult

from models.schema import ResumeData

class PDFGenerator:
    def __init__(self, credentials_path):
        self.credentials_path = credentials_path
    
    def _get_credentials(self):
        """Initialize credentials from file."""
        # Looking at the example code, it appears credentials should be directly 
        # initialized with environment variables, not from the file
        
        # Get credentials from environment variables
        client_id = os.getenv('PDF_SERVICES_CLIENT_ID')
        client_secret = os.getenv('PDF_SERVICES_CLIENT_SECRET')
        
        # Create credentials
        credentials = ServicePrincipalCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
            
        return credentials
        
    def generate_resume(self, resume_data: ResumeData, template_path: str):
        """Generate both DOCX and PDF versions of resume from template and data."""
        try:
            # Create temporary directory to store outputs
            with tempfile.TemporaryDirectory() as temp_dir:
                # Convert ResumeData to JSON string
                json_data_for_merge = resume_data.model_dump()
                
                # Process employment history for template if available
                if hasattr(resume_data, 'employment_history') and resume_data.employment_history:
                    # Format employment history for the template
                    json_data_for_merge['formatted_employment_history'] = []
                    for job in resume_data.employment_history:
                        json_data_for_merge['formatted_employment_history'].append({
                            'company_name': job.company_name,
                            'period': job.period,
                            'location': job.location
                        })
                
                # Process experiences with the new structure
                if hasattr(resume_data, 'experiences') and resume_data.experiences:
                    # Format experiences for the template
                    json_data_for_merge['formatted_experiences'] = []
                    for exp in resume_data.experiences:
                        # Extract bullet points as strings
                        bullet_points = [bp.bullet_point for bp in exp.bullet_points]
                        
                        json_data_for_merge['formatted_experiences'].append({
                            'company': exp.company_info.name,
                            'period': exp.company_info.period,
                            'location': exp.company_info.location,
                            'job_title': exp.job_title,
                            'bullet_points': bullet_points
                        })
                
                # Read the template file
                with open(template_path, 'rb') as file:
                    input_stream = file.read()
                
                # Initialize credentials
                credentials = self._get_credentials()
                
                # Create PDF Services instance
                pdf_services = PDFServices(credentials=credentials)
                
                # Upload the template asset
                input_asset = pdf_services.upload(input_stream=input_stream,
                                                 mime_type=PDFServicesMediaType.DOCX)
                
                # Generate DOCX
                docx_path = os.path.join(temp_dir, "resume.docx")
                docx_content = self._merge_document(
                    pdf_services, input_asset, json_data_for_merge, 
                    OutputFormat.DOCX, docx_path
                )
                
                # Generate PDF
                pdf_path = os.path.join(temp_dir, "resume.pdf")
                pdf_content = self._merge_document(
                    pdf_services, input_asset, json_data_for_merge, 
                    OutputFormat.PDF, pdf_path
                )
                
                return {
                    "docx": docx_content,
                    "pdf": pdf_content
                }
                
        except (ServiceApiException, ServiceUsageException, SdkException) as e:
            raise Exception(f"Error generating document: {str(e)}")
    
    def _merge_document(self, pdf_services, input_asset, json_data, output_format, output_path):
        """Merges document template with JSON data and saves to output path."""
        try:
            # Create parameters for the job
            document_merge_params = DocumentMergeParams(
                json_data_for_merge=json_data,
                output_format=output_format
            )
            
            # Create a new job instance
            document_merge_job = DocumentMergeJob(
                input_asset=input_asset,
                document_merge_params=document_merge_params
            )
            
            # Submit the job and get the job result
            location = pdf_services.submit(document_merge_job)
            pdf_services_response = pdf_services.get_job_result(location, DocumentMergePDFResult)
            
            # Get content from the resulting asset
            result_asset = pdf_services_response.get_result().get_asset()
            stream_asset = pdf_services.get_content(result_asset)
            
            # Save the content to output path
            with open(output_path, "wb") as file:
                file.write(stream_asset.get_input_stream())
            
            # Read the file back for returning
            with open(output_path, 'rb') as file:
                return file.read()
                
        except (ServiceApiException, ServiceUsageException, SdkException) as e:
            raise Exception(f"Error in document merge: {str(e)}") 
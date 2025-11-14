"""
Business logic services for the Data Extraction Service.

This module contains the core business logic for processing extraction jobs,
integrating with external APIs, and managing job lifecycle.
"""
import logging
import time
from typing import List, Dict, Any
from django.utils import timezone

from .models import Job, ExtractionResult
from tests.mocks.external_api_mock import (
    MockExternalAPI,
    MockAuthenticationError,
    MockRateLimitError,
    MockServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class ExtractionService:
    """
    Service for processing data extraction jobs.
    
    This service handles the complete extraction workflow:
    1. Authenticate with external API
    2. Fetch data from external API
    3. Store results in database
    4. Update job status
    """
    
    def __init__(self):
        """Initialize the extraction service."""
        self.external_api = MockExternalAPI()
    
    def process_extraction(self, job_id: str, api_token: str, record_type: str = 'contacts'):
        """
        Process an extraction job.
        
        This method runs in a background thread and handles the complete
        extraction workflow from start to finish.
        
        Args:
            job_id: UUID of the job to process
            api_token: API token for the external service
            record_type: Type of records to extract ('contacts' or 'users')
        """
        try:
            # Get the job
            job = Job.objects.get(id=job_id)
            
            # Mark job as started
            logger.info(f"Starting extraction job {job_id}")
            job.mark_as_started()
            
            # Authenticate with external API
            logger.info(f"Authenticating with external API for job {job_id}")
            try:
                self.external_api.authenticate(api_token)
            except MockAuthenticationError as e:
                logger.error(f"Authentication failed for job {job_id}: {e}")
                job.mark_as_failed(f"Authentication failed: {str(e)}")
                return
            
            # Fetch data from external API
            logger.info(f"Fetching {record_type} data for job {job_id}")
            all_records = []
            
            try:
                all_records = self.fetch_all_records(api_token, record_type)
            except MockRateLimitError as e:
                logger.error(f"Rate limit exceeded for job {job_id}: {e}")
                job.mark_as_failed(f"Rate limit exceeded: {str(e)}")
                return
            except MockServiceUnavailableError as e:
                logger.error(f"External service unavailable for job {job_id}: {e}")
                job.mark_as_failed(f"External service unavailable: {str(e)}")
                return
            except Exception as e:
                logger.error(f"Error fetching data for job {job_id}: {e}")
                job.mark_as_failed(f"Error fetching data: {str(e)}")
                return
            
            # Store results in database
            logger.info(f"Storing {len(all_records)} records for job {job_id}")
            self.store_results(job, all_records)
            
            # Mark job as completed
            job.mark_as_completed(record_count=len(all_records))
            logger.info(f"Extraction job {job_id} completed successfully with {len(all_records)} records")
            
        except Job.DoesNotExist:
            logger.error(f"Job {job_id} not found")
        except Exception as e:
            logger.error(f"Unexpected error processing job {job_id}: {e}", exc_info=True)
            try:
                job = Job.objects.get(id=job_id)
                job.mark_as_failed(f"Unexpected error: {str(e)}")
            except:
                pass
    
    def fetch_all_records(self, api_token: str, record_type: str) -> List[Dict[str, Any]]:
        """
        Fetch all records from the external API with pagination.
        
        Args:
            api_token: API token for authentication
            record_type: Type of records to fetch
            
        Returns:
            List of all fetched records
        """
        all_records = []
        page = 1
        max_pages = 10  # Limit to prevent infinite loops
        
        while page <= max_pages:
            try:
                # Fetch data for current page
                response = self.external_api.fetch_data(
                    token=api_token,
                    record_type=record_type,
                    page=page,
                    per_page=100
                )
                
                # Extract records from response
                records = response.get('data', [])
                all_records.extend(records)
                
                # Check if there are more pages
                pagination = response.get('pagination', {})
                has_more = pagination.get('has_more', False)
                
                if not has_more:
                    break
                
                page += 1
                
                # Small delay to respect rate limits
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                raise
        
        return all_records
    
    def store_results(self, job: Job, records: List[Dict[str, Any]]):
        """
        Store extraction results in the database.
        
        Args:
            job: The job these results belong to
            records: List of record dictionaries to store
        """
        # Create ExtractionResult objects in bulk for efficiency
        result_objects = [
            ExtractionResult(
                job=job,
                data=record,
                created_at=timezone.now()
            )
            for record in records
        ]
        
        # Bulk create all results
        ExtractionResult.objects.bulk_create(result_objects, batch_size=500)
        
        logger.info(f"Stored {len(result_objects)} results for job {job.id}")
    
    def validate_token(self, api_token: str) -> bool:
        """
        Validate an API token.
        
        Args:
            api_token: Token to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            self.external_api.authenticate(api_token)
            return True
        except MockAuthenticationError:
            return False


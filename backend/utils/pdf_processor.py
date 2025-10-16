"""
PDF processing utilities for screenplay files
"""
import io
from typing import Tuple, Optional
import httpx
from PyPDF2 import PdfReader

from .logging import get_logger
from ..services.storage import StorageService

logger = get_logger("pdf_processor")


class PDFProcessor:
    """Process PDF files to extract text and metadata"""
    
    @staticmethod
    async def extract_text_from_url(pdf_url: str) -> Tuple[str, int]:
        """
        Download PDF from URL and extract text content
        
        Args:
            pdf_url: URL to the PDF file
            
        Returns:
            Tuple of (extracted_text, page_count)
            
        Raises:
            Exception: If PDF download or processing fails
        """
        try:
            # Special handling for S3 URLs
            logger.info("processing_pdf_url", url=pdf_url)
            if "s3.amazonaws.com" in pdf_url or ".s3.amazonaws.com" in pdf_url:
                try:
                    # Extract the key directly from the URL - handles both URL formats:
                    # https://s3.amazonaws.com/bucket-name/key
                    # https://bucket-name.s3.amazonaws.com/key
                    
                    if "https://s3.amazonaws.com/" in pdf_url:
                        # Format: https://s3.amazonaws.com/bucket-name/key
                        parts = pdf_url.split("https://s3.amazonaws.com/")
                        if len(parts) > 1:
                            path = parts[1].split("?")[0]  # Remove query parameters
                            parts = path.split("/", 1)
                            bucket_name = parts[0]
                            key = parts[1] if len(parts) > 1 else ""
                    elif ".s3.amazonaws.com/" in pdf_url:
                        # Format: https://bucket-name.s3.amazonaws.com/key
                        parts = pdf_url.split(".s3.amazonaws.com/")
                        if len(parts) > 1:
                            bucket_parts = parts[0].split("//")
                            bucket_name = bucket_parts[-1]
                            key = parts[1].split("?")[0]  # Remove query parameters
                    
                    # If the key doesn't contain 'screenplay/', add it as a prefix
                    if key and not key.startswith("screenplay/"):
                        key = f"screenplay/{key}"
                    
                    logger.info("extracted_s3_info", bucket=bucket_name, key=key)
                    
                    # Create a presigned URL for GET access
                    storage_service = StorageService()
                    presigned_url = storage_service.create_presigned_get_url(key)
                    pdf_url = presigned_url  # Use the presigned URL instead
                    logger.info("using_presigned_url", presigned_url=presigned_url, key=key)
                except Exception as e:
                    logger.error("presigned_url_creation_failed", error=str(e), url=pdf_url)
                    # Continue with original URL if extraction fails
                
            # Download PDF from URL
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(pdf_url)
                response.raise_for_status()
                pdf_content = response.content
            
            # Process PDF
            pdf_file = io.BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            
            page_count = len(reader.pages)
            
            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text:
                        text_parts.append(f"--- Page {page_num} ---\n{text}\n")
                except Exception as e:
                    logger.warning(
                        "page_extraction_failed",
                        page_num=page_num,
                        error=str(e)
                    )
                    text_parts.append(f"--- Page {page_num} ---\n[Text extraction failed]\n")
            
            full_text = "\n".join(text_parts)
            
            logger.info(
                "pdf_processed",
                page_count=page_count,
                text_length=len(full_text)
            )
            
            return full_text, page_count
            
        except httpx.HTTPError as e:
            logger.error("pdf_download_failed", error=str(e), url=pdf_url)
            raise Exception(f"Failed to download PDF: {str(e)}")
        except Exception as e:
            logger.error("pdf_processing_failed", error=str(e))
            raise Exception(f"Failed to process PDF: {str(e)}")
    
    @staticmethod
    def extract_text_from_bytes(pdf_bytes: bytes) -> Tuple[str, int]:
        """
        Extract text from PDF bytes
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            Tuple of (extracted_text, page_count)
            
        Raises:
            Exception: If PDF processing fails
        """
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)
            
            page_count = len(reader.pages)
            
            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text:
                        text_parts.append(f"--- Page {page_num} ---\n{text}\n")
                except Exception as e:
                    logger.warning(
                        "page_extraction_failed",
                        page_num=page_num,
                        error=str(e)
                    )
                    text_parts.append(f"--- Page {page_num} ---\n[Text extraction failed]\n")
            
            full_text = "\n".join(text_parts)
            
            logger.info(
                "pdf_processed",
                page_count=page_count,
                text_length=len(full_text)
            )
            
            return full_text, page_count
            
        except Exception as e:
            logger.error("pdf_processing_failed", error=str(e))
            raise Exception(f"Failed to process PDF: {str(e)}")

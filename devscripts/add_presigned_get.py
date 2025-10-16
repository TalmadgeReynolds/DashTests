#!/usr/bin/env python3
"""
Script to add presigned GET URL support to the storage service
"""
import sys
import os

# Add parent directory to path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.storage import StorageService

def create_presigned_get_method():
    """Add a method to the StorageService class to generate presigned GET URLs"""
    code_to_add = """
    def create_presigned_get_url(self, key: str, expires_in: int = 3600) -> str:
        \"\"\"
        Generate a presigned GET URL for accessing a file
        
        Args:
            key: The storage key of the file
            expires_in: Expiration time in seconds
            
        Returns:
            Presigned URL for GET access
        \"\"\"
        if self.mock_mode:
            return f"http://mock-storage/{self.bucket}/{key}"
        
        try:
            # Create presigned GET URL
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": key
                },
                ExpiresIn=expires_in
            )
            
            logger.info("presigned_get_url_created", key=key, expires_in=expires_in)
            return url
            
        except ClientError as e:
            logger.error("presign_get_failed", error=str(e), key=key)
            raise StorageError(f"Failed to generate presigned GET URL: {str(e)}")
    """
    
    # Print the code that needs to be added
    print("Add this method to the StorageService class in backend/services/storage.py:")
    print(code_to_add)
    
    # Suggest modification to the pdf_processor.py file
    pdf_processor_change = """
    # In backend/utils/pdf_processor.py
    # Modify the extract_text_from_url method to handle S3 URLs
    
    from ..services.storage import StorageService
    
    @staticmethod
    async def extract_text_from_url(pdf_url: str) -> Tuple[str, int]:
        try:
            # Special handling for S3 URLs
            if "s3.amazonaws.com" in pdf_url:
                # Extract the key from the URL
                bucket_name = pdf_url.split("s3.amazonaws.com/")[1].split("/")[0]
                key = pdf_url.split(bucket_name + "/")[1].split("?")[0]
                
                # Create a presigned URL for GET access
                storage_service = StorageService()
                presigned_url = storage_service.create_presigned_get_url(key)
                pdf_url = presigned_url  # Use the presigned URL instead
            
            # Continue with the existing implementation
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(pdf_url)
                response.raise_for_status()
                pdf_content = response.content
            
            # Rest of the method remains unchanged
    """
    
    print("\nThen modify the pdf_processor.py file:")
    print(pdf_processor_change)

if __name__ == "__main__":
    create_presigned_get_method()
"""
AWS S3 photo upload utility for PD Triglav trip reports
Handles secure photo uploads with metadata extraction
"""

import os
import uuid
import boto3
import mimetypes
from datetime import datetime
from PIL import Image
from flask import current_app
from botocore.exceptions import ClientError, NoCredentialsError
from werkzeug.utils import secure_filename


class S3PhotoUploader:
    """Handles photo uploads to AWS S3 with metadata extraction"""
    
    def __init__(self):
        """Initialize S3 client with app configuration"""
        self.s3_client = None
        self.bucket_name = None
        self._initialize_s3()
    
    def _initialize_s3(self):
        """Initialize S3 client from Flask configuration"""
        try:
            config = current_app.config
            
            self.bucket_name = config.get('AWS_S3_BUCKET')
            if not self.bucket_name:
                raise ValueError("AWS_S3_BUCKET not configured")
            
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=config.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=config.get('AWS_SECRET_ACCESS_KEY'),
                region_name=config.get('AWS_REGION', 'eu-north-1')
            )
            
        except Exception as e:
            current_app.logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def generate_s3_key(self, trip_report_id, original_filename):
        """Generate unique S3 key for photo storage
        
        Format: trip-reports/YYYY/MM/report-{id}/photo-{uuid}.{ext}
        """
        # Extract file extension
        file_ext = os.path.splitext(secure_filename(original_filename))[1].lower()
        if not file_ext:
            file_ext = '.jpg'  # Default extension
        
        # Generate unique filename
        unique_id = uuid.uuid4().hex
        filename = f"photo-{unique_id}{file_ext}"
        
        # Create date-based path
        now = datetime.utcnow()
        date_path = now.strftime('%Y/%m')
        
        # Full S3 key
        s3_key = f"trip-reports/{date_path}/report-{trip_report_id}/{filename}"
        
        return s3_key
    
    def extract_image_metadata(self, file_obj):
        """Extract image metadata using PIL
        
        Returns dict with width, height, file_size, content_type
        """
        try:
            # Reset file pointer
            file_obj.seek(0)
            
            # Get file size
            file_obj.seek(0, 2)  # Seek to end
            file_size = file_obj.tell()
            file_obj.seek(0)  # Reset to beginning
            
            # Get MIME type
            content_type = file_obj.content_type or 'image/jpeg'
            
            # Extract image dimensions
            try:
                with Image.open(file_obj) as img:
                    width, height = img.size
                file_obj.seek(0)  # Reset after PIL reads
            except Exception:
                # If PIL fails, use defaults
                width = height = None
            
            return {
                'file_size': file_size,
                'width': width,
                'height': height,
                'content_type': content_type
            }
            
        except Exception as e:
            current_app.logger.warning(f"Failed to extract image metadata: {e}")
            return {
                'file_size': None,
                'width': None,
                'height': None,
                'content_type': 'image/jpeg'
            }
    
    def upload_photo(self, file_obj, trip_report_id, caption=None):
        """Upload photo to S3 and return photo metadata
        
        Args:
            file_obj: FileStorage object from form
            trip_report_id: ID of the trip report
            caption: Optional photo caption
            
        Returns:
            dict: Photo metadata for database storage
            
        Raises:
            Exception: If upload fails
        """
        if not file_obj or not file_obj.filename:
            raise ValueError("No file provided")
        
        try:
            # Generate S3 key
            s3_key = self.generate_s3_key(trip_report_id, file_obj.filename)
            
            # Extract image metadata
            metadata = self.extract_image_metadata(file_obj)
            
            # Upload to S3
            file_obj.seek(0)  # Ensure we're at the beginning
            
            extra_args = {
                'ContentType': metadata['content_type'],
                'Metadata': {
                    'original-filename': secure_filename(file_obj.filename),
                    'trip-report-id': str(trip_report_id),
                    'upload-date': datetime.utcnow().isoformat()
                }
            }
            
            # Perform the upload
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            current_app.logger.info(f"Successfully uploaded photo to S3: {s3_key}")
            
            # Return photo metadata for database
            return {
                'filename': os.path.basename(s3_key),
                'original_filename': file_obj.filename,
                'caption': caption,
                's3_key': s3_key,
                's3_bucket': self.bucket_name,
                'file_size': metadata['file_size'],
                'width': metadata['width'],
                'height': metadata['height'],
                'content_type': metadata['content_type']
            }
            
        except NoCredentialsError:
            current_app.logger.error("AWS credentials not found")
            raise Exception("AWS configuration error")
        except ClientError as e:
            current_app.logger.error(f"AWS S3 error: {e}")
            raise Exception(f"Upload failed: {e}")
        except Exception as e:
            current_app.logger.error(f"Photo upload error: {e}")
            raise Exception(f"Upload failed: {e}")
    
    def delete_photo(self, s3_key):
        """Delete photo from S3
        
        Args:
            s3_key: S3 object key to delete
            
        Returns:
            bool: True if successful
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            current_app.logger.info(f"Successfully deleted photo from S3: {s3_key}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to delete photo from S3: {e}")
            return False
    
    def get_photo_url(self, s3_key, expires_in=3600):
        """Generate presigned URL for photo access
        
        Args:
            s3_key: S3 object key
            expires_in: URL expiration time in seconds (default 1 hour)
            
        Returns:
            str: Presigned URL or public URL
        """
        try:
            # For now, return public URL (works if bucket allows public read)
            # TODO: Implement presigned URLs for better security
            region = current_app.config.get('AWS_REGION', 'eu-north-1')
            return f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
            
        except Exception as e:
            current_app.logger.error(f"Failed to generate photo URL: {e}")
            return None


def upload_photos_for_report(photos, trip_report_id):
    """Convenience function to upload multiple photos for a trip report
    
    Args:
        photos: List of FileStorage objects
        trip_report_id: ID of the trip report
        
    Returns:
        list: List of photo metadata dicts for database storage
        
    Raises:
        Exception: If any upload fails
    """
    if not photos:
        return []
    
    uploader = S3PhotoUploader()
    uploaded_photos = []
    
    for i, photo in enumerate(photos):
        if photo and photo.filename:
            try:
                photo_metadata = uploader.upload_photo(
                    photo, 
                    trip_report_id,
                    caption=f"Fotografija {i + 1}"  # Default caption
                )
                uploaded_photos.append(photo_metadata)
                
            except Exception as e:
                # Cleanup any already uploaded photos
                for uploaded in uploaded_photos:
                    uploader.delete_photo(uploaded['s3_key'])
                raise Exception(f"Failed to upload photo '{photo.filename}': {e}")
    
    return uploaded_photos
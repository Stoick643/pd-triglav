"""
Mock AWS S3 services for testing
Provides realistic S3 responses without making real AWS calls
"""

import io
from typing import Dict, List, Optional, BinaryIO
from PIL import Image


class MockS3Client:
    """Mock S3 client that simulates AWS S3 operations"""

    def __init__(self):
        self._uploaded_files = {}
        self._call_count = 0

    def upload_fileobj(self, fileobj: BinaryIO, bucket: str, key: str, **kwargs) -> Dict:
        """Mock S3 file upload"""
        self._call_count += 1

        # Read file content for validation
        content = fileobj.read()
        fileobj.seek(0)  # Reset file pointer

        # Simulate upload success
        self._uploaded_files[key] = {
            "bucket": bucket,
            "size": len(content),
            "content_type": kwargs.get("ContentType", "application/octet-stream"),
            "metadata": kwargs.get("Metadata", {}),
            "upload_id": f"mock-upload-{self._call_count}",
        }

        return {"ETag": f'"mock-etag-{self._call_count}"', "ServerSideEncryption": "AES256"}

    def delete_object(self, Bucket: str, Key: str) -> Dict:
        """Mock S3 file deletion"""
        if Key in self._uploaded_files:
            del self._uploaded_files[Key]

        return {"DeleteMarker": False, "VersionId": f"mock-version-{self._call_count}"}

    def head_object(self, Bucket: str, Key: str) -> Dict:
        """Mock S3 object metadata retrieval"""
        if Key not in self._uploaded_files:
            raise Exception("NoSuchKey")

        file_info = self._uploaded_files[Key]
        return {
            "ContentLength": file_info["size"],
            "ContentType": file_info["content_type"],
            "ETag": f'"mock-etag-{Key}"',
            "LastModified": "2025-01-29T10:00:00Z",
            "Metadata": file_info.get("metadata", {}),
        }

    def list_objects_v2(self, Bucket: str, Prefix: str = "") -> Dict:
        """Mock S3 object listing"""
        matching_objects = []
        for key, info in self._uploaded_files.items():
            if key.startswith(Prefix):
                matching_objects.append(
                    {
                        "Key": key,
                        "Size": info["size"],
                        "ETag": f'"mock-etag-{key}"',
                        "LastModified": "2025-01-29T10:00:00Z",
                    }
                )

        return {
            "Contents": matching_objects,
            "KeyCount": len(matching_objects),
            "IsTruncated": False,
        }


class MockS3PhotoUploader:
    """Mock S3 photo uploader that simulates photo upload operations"""

    def __init__(self, bucket_name: str = "mock-bucket"):
        self.bucket_name = bucket_name
        self.s3_client = MockS3Client()
        self._processed_photos = []

    def upload_photo(
        self, file_stream: BinaryIO, filename: str, metadata: Optional[Dict] = None
    ) -> Dict:
        """Mock photo upload with image processing"""

        # Simulate image validation
        try:
            file_stream.seek(0)
            img = Image.open(file_stream)
            width, height = img.size
            format_type = img.format
            file_stream.seek(0)
        except Exception:
            raise ValueError("Invalid image file")

        # Generate mock S3 key
        key = f"photos/{filename}"

        # Mock upload to S3
        upload_result = self.s3_client.upload_fileobj(
            file_stream,
            self.bucket_name,
            key,
            ContentType=f"image/{format_type.lower()}",
            Metadata=metadata or {},
        )

        # Generate mock thumbnail (simulate processing)
        thumbnail_key = f"thumbnails/{filename}"
        thumbnail_stream = io.BytesIO(b"mock_thumbnail_data")
        self.s3_client.upload_fileobj(
            thumbnail_stream,
            self.bucket_name,
            thumbnail_key,
            ContentType=f"image/{format_type.lower()}",
        )

        result = {
            "original_url": f"https://{self.bucket_name}.s3.amazonaws.com/{key}",
            "thumbnail_url": f"https://{self.bucket_name}.s3.amazonaws.com/{thumbnail_key}",
            "filename": filename,
            "size": len(file_stream.read()),
            "width": width,
            "height": height,
            "format": format_type,
            "key": key,
            "thumbnail_key": thumbnail_key,
        }

        self._processed_photos.append(result)
        return result

    def delete_photo(self, key: str) -> bool:
        """Mock photo deletion"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            # Also delete thumbnail
            if key.startswith("photos/"):
                thumbnail_key = key.replace("photos/", "thumbnails/")
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=thumbnail_key)
            return True
        except Exception:
            return False

    def get_photo_info(self, key: str) -> Dict:
        """Mock photo info retrieval"""
        return self.s3_client.head_object(Bucket=self.bucket_name, Key=key)

    def list_photos(self, prefix: str = "photos/") -> List[Dict]:
        """Mock photo listing"""
        result = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
        return result.get("Contents", [])


class MockBoto3:
    """Mock boto3 module"""

    @staticmethod
    def client(service_name: str, **kwargs):
        """Mock boto3.client() function"""
        if service_name == "s3":
            return MockS3Client()
        else:
            raise ValueError(f"Unsupported service: {service_name}")


def create_mock_image(width: int = 100, height: int = 100, format: str = "JPEG") -> io.BytesIO:
    """Create a mock image file for testing"""
    img = Image.new("RGB", (width, height), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format=format)
    img_bytes.seek(0)
    return img_bytes


def create_large_mock_image(width: int = 3000, height: int = 3000) -> io.BytesIO:
    """Create a large mock image for size testing"""
    return create_mock_image(width, height)


def create_invalid_file() -> io.BytesIO:
    """Create an invalid file that's not an image"""
    return io.BytesIO(b"This is not an image file")


# Patch helpers for S3 testing
def patch_s3_services():
    """Returns patches for S3 service components"""
    return [
        ("boto3.client", MockBoto3.client),
        ("utils.s3_upload.S3PhotoUploader", MockS3PhotoUploader),
    ]


def patch_boto3():
    """Returns patch for boto3 module"""
    return ("boto3", MockBoto3())


# Common test scenarios
MOCK_S3_RESPONSES = {
    "upload_success": {
        "original_url": "https://mock-bucket.s3.amazonaws.com/photos/test.jpg",
        "thumbnail_url": "https://mock-bucket.s3.amazonaws.com/thumbnails/test.jpg",
        "filename": "test.jpg",
        "size": 1024,
        "width": 800,
        "height": 600,
        "format": "JPEG",
    },
    "upload_error": {
        "error": "InvalidImageFormat",
        "message": "The provided file is not a valid image",
    },
    "file_too_large": {
        "error": "FileTooLarge",
        "message": "File size exceeds maximum allowed size",
    },
}

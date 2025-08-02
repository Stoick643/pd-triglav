"""
Test cases for photo upload functionality (Step 2E.1)
"""

import pytest
import io
import os
from unittest.mock import Mock, patch
from PIL import Image
from werkzeug.datastructures import FileStorage

from app import create_app
from models.user import db, User, UserRole
from models.trip import Trip, TripDifficulty, TripStatus
from models.content import TripReport, Photo

# Mark all tests in this file as slow external service tests (S3)
pytestmark = [pytest.mark.slow, pytest.mark.external]
from utils.s3_upload import S3PhotoUploader


@pytest.fixture
def app():
    """Create test app"""
    import tempfile
    from config import TestingConfig

    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    TestingConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()

        # Create test user
        user = User(
            email="test@pd-triglav.si", name="Test User", role=UserRole.MEMBER, is_approved=True
        )
        user.set_password("password123")
        db.session.add(user)

        # Create test trip
        from datetime import date

        trip = Trip(
            title="Test Trip",
            destination="Test Mountain",
            trip_date=date(2025, 8, 1),
            difficulty=TripDifficulty.MODERATE,
            status=TripStatus.ANNOUNCED,
            leader_id=1,
        )
        db.session.add(trip)

        # Create test trip report
        report = TripReport(
            title="Test Report", content="Test content", trip_id=1, author_id=1, is_published=True
        )
        db.session.add(report)

        db.session.commit()

        yield app

        db.drop_all()

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def auth_client(client, app):
    """Create authenticated client"""
    with app.app_context():
        user = User.query.filter_by(email="test@pd-triglav.si").first()

        with client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

    return client


def create_test_image(filename="test.jpg", size=(800, 600), format="JPEG"):
    """Create test image file"""
    img = Image.new("RGB", size, color="red")
    img_io = io.BytesIO()
    img.save(img_io, format=format)
    img_io.seek(0)

    return FileStorage(stream=img_io, filename=filename, content_type=f"image/{format.lower()}")


class TestS3PhotoUploader:
    """Test S3PhotoUploader utility class"""

    def test_generate_s3_key(self, app):
        """Test S3 key generation"""
        with app.app_context():
            uploader = S3PhotoUploader()

            # Test with simple filename
            key = uploader.generate_s3_key(123, "test.jpg")
            assert key.startswith("trip-reports/2025/07/report-123/")
            assert key.endswith(".jpg")
            assert "photo-" in key

            # Test with complex filename
            key = uploader.generate_s3_key(456, "My Photo File (1).PNG")
            assert "report-456" in key
            assert key.endswith(".png")  # Should be lowercase

    def test_extract_image_metadata(self, app):
        """Test image metadata extraction"""
        with app.app_context():
            uploader = S3PhotoUploader()
            test_image = create_test_image("test.jpg", (800, 600))

            metadata = uploader.extract_image_metadata(test_image)

            assert metadata["width"] == 800
            assert metadata["height"] == 600
            assert metadata["content_type"] == "image/jpeg"
            assert metadata["file_size"] > 0

    @patch("utils.s3_upload.boto3.client")
    def test_upload_photo_success(self, mock_boto_client, app):
        """Test successful photo upload"""
        with app.app_context():
            # Mock S3 client
            mock_s3 = Mock()
            mock_boto_client.return_value = mock_s3

            # Set up test config
            app.config["AWS_S3_BUCKET"] = "test-bucket"
            app.config["AWS_ACCESS_KEY_ID"] = "test-key"
            app.config["AWS_SECRET_ACCESS_KEY"] = "test-secret"
            app.config["AWS_REGION"] = "eu-north-1"

            uploader = S3PhotoUploader()
            test_image = create_test_image("test.jpg")

            result = uploader.upload_photo(test_image, 123, "Test caption")

            # Verify upload was called
            mock_s3.upload_fileobj.assert_called_once()

            # Verify returned metadata
            assert result["filename"].endswith(".jpg")
            assert result["original_filename"] == "test.jpg"
            assert result["caption"] == "Test caption"
            assert result["s3_bucket"] == "test-bucket"
            assert "trip-reports/2025/07/report-123/" in result["s3_key"]

    @patch("utils.s3_upload.boto3.client")
    def test_upload_photo_failure(self, mock_boto_client, app):
        """Test photo upload failure"""
        with app.app_context():
            # Set up test config
            app.config["AWS_S3_BUCKET"] = "test-bucket"
            app.config["AWS_ACCESS_KEY_ID"] = "test-key"
            app.config["AWS_SECRET_ACCESS_KEY"] = "test-secret"

            # Mock S3 client to raise exception
            mock_s3 = Mock()
            mock_s3.upload_fileobj.side_effect = Exception("S3 Error")
            mock_boto_client.return_value = mock_s3

            uploader = S3PhotoUploader()
            test_image = create_test_image("test.jpg")

            with pytest.raises(Exception, match="Upload failed"):
                uploader.upload_photo(test_image, 123)


class TestPhotoUploadIntegration:
    """Test photo upload integration with forms and routes"""

    @patch("utils.s3_upload.boto3.client")
    def test_trip_report_with_photos(self, mock_boto_client, auth_client, app):
        """Test creating trip report with photos"""
        with app.app_context():
            # Set up test config
            app.config["AWS_S3_BUCKET"] = "test-bucket"
            app.config["AWS_ACCESS_KEY_ID"] = "test-key"
            app.config["AWS_SECRET_ACCESS_KEY"] = "test-secret"

            # Mock S3 client
            mock_s3 = Mock()
            mock_boto_client.return_value = mock_s3

            # Create test images
            photo1 = create_test_image("photo1.jpg")
            photo2 = create_test_image("photo2.png", format="PNG")

            # Submit trip report with photos
            response = auth_client.post(
                "/reports/create",
                data={
                    "trip_id": "1",
                    "title": "Test Report with Photos",
                    "content": "This is a test report with photos.",
                    "is_published": "true",
                    "photos": [photo1, photo2],
                },
                content_type="multipart/form-data",
            )

            # Should redirect on success
            assert response.status_code == 302

            # Verify photos were uploaded to S3
            assert mock_s3.upload_fileobj.call_count == 2

            # Verify photos in database
            photos = Photo.query.all()
            assert len(photos) >= 2

            # Verify photo metadata
            latest_photos = Photo.query.order_by(Photo.id.desc()).limit(2).all()
            for photo in latest_photos:
                assert photo.trip_report_id is not None
                assert photo.uploaded_by == 1  # Test user ID
                assert photo.s3_key.startswith("trip-reports/")
                assert photo.file_size > 0

    def test_photo_validation_file_type(self, auth_client, app):
        """Test photo file type validation"""
        with app.app_context():
            # Create invalid file (text file)
            invalid_file = FileStorage(
                stream=io.BytesIO(b"This is not an image"),
                filename="test.txt",
                content_type="text/plain",
            )

            response = auth_client.post(
                "/reports/create",
                data={
                    "trip_id": "1",
                    "title": "Test Report",
                    "content": "Test content",
                    "is_published": "true",
                    "photos": [invalid_file],
                },
                content_type="multipart/form-data",
            )

            # Should show form with validation error
            assert response.status_code == 200
            assert "Dovoljene so samo slike".encode("utf-8") in response.data

    def test_photo_validation_file_size(self, auth_client, app):
        """Test photo file size validation"""
        with app.app_context():
            # Create oversized file (mock 15MB file)
            large_file = FileStorage(
                stream=io.BytesIO(b"x" * (15 * 1024 * 1024)),  # 15MB
                filename="large.jpg",
                content_type="image/jpeg",
            )

            response = auth_client.post(
                "/reports/create",
                data={
                    "trip_id": "1",
                    "title": "Test Report",
                    "content": "Test content",
                    "is_published": "true",
                    "photos": [large_file],
                },
                content_type="multipart/form-data",
            )

            # Should show form with validation error
            assert response.status_code == 200
            assert "presegati 10 MB".encode("utf-8") in response.data

    def test_too_many_photos(self, auth_client, app):
        """Test validation of too many photos"""
        with app.app_context():
            # Create 11 photos (exceeds limit of 10)
            photos = [create_test_image(f"photo{i}.jpg") for i in range(11)]

            response = auth_client.post(
                "/reports/create",
                data={
                    "trip_id": "1",
                    "title": "Test Report",
                    "content": "Test content",
                    "is_published": "true",
                    "photos": photos,
                },
                content_type="multipart/form-data",
            )

            # Should show form with validation error
            assert response.status_code == 200
            assert "največ 10 fotografij".encode("utf-8") in response.data


class TestPhotoModel:
    """Test Photo model functionality"""

    def test_photo_url_property(self, app):
        """Test photo URL generation"""
        with app.app_context():
            photo = Photo(
                filename="test.jpg",
                s3_key="trip-reports/2025/07/report-1/photo-abc123.jpg",
                s3_bucket="pd-triglav-photos",
            )

            url = photo.url
            assert "pd-triglav-photos.s3.eu-north-1.amazonaws.com" in url
            assert "trip-reports/2025/07/report-1/photo-abc123.jpg" in url

    def test_photo_relationships(self, app):
        """Test photo database relationships"""
        with app.app_context():
            # Get existing data
            report = TripReport.query.first()
            user = User.query.first()

            # Create photo
            photo = Photo(
                filename="test.jpg",
                s3_key="test-key",
                s3_bucket="test-bucket",
                trip_report_id=report.id,
                uploaded_by=user.id,
            )
            db.session.add(photo)
            db.session.commit()

            # Test relationships
            assert photo.trip_report == report
            assert photo.uploader == user
            assert photo in report.photos
            assert photo in user.uploaded_photos


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

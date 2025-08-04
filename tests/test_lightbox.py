"""
Test suite for PD Triglav Photo Lightbox functionality
Tests both JavaScript behavior and Python integration
"""

import pytest
from flask import url_for
from models.user import User, UserRole, db
from models.content import TripReport, Photo
from models.trip import Trip, TripDifficulty
from datetime import datetime, timedelta


@pytest.mark.fast
class TestLightboxIntegration:
    """Test lightbox integration with report photos"""

    def test_lightbox_scripts_loaded_on_report_page(self, client, test_user_member):
        """Test that lightbox JS and CSS are included on report pages"""
        # Create a trip and report with photos
        trip = Trip(
            title="Test Trip",
            description="Test description",
            destination="Test Mountain",
            trip_date=datetime.now() + timedelta(days=7),
            difficulty=TripDifficulty.MODERATE,
            max_participants=10,
            leader_id=test_user_member.id,
        )
        db.session.add(trip)
        db.session.commit()

        report = TripReport(
            title="Test Report with Photos",
            content="Test content",
            trip_id=trip.id,
            author_id=test_user_member.id,
            is_published=True,
        )
        db.session.add(report)
        db.session.commit()

        # Add test photos
        photo1 = Photo(
            trip_report_id=report.id,
            filename="photo1.jpg",
            s3_key="photos/photo1.jpg",
            s3_bucket="test-bucket",
            uploaded_by=test_user_member.id,
            caption="Mountain peak view",
            width=1920,
            height=1080,
            file_size=1024000,
        )
        db.session.add(photo1)
        db.session.commit()

        # Access report detail page
        response = client.get(url_for("reports.view_report", report_id=report.id))
        assert response.status_code == 200

        # Check for lightbox resources
        assert b"lightbox.js" in response.data
        assert b"lightbox.css" in response.data
        assert b"photo-link" in response.data
        assert b"photo-mosaic" in response.data

    def test_photo_links_no_target_blank(self, client, test_user_member):
        """Test that photo links don't have target='_blank' anymore"""
        # Create report with photos
        trip = Trip(
            title="Test Trip",
            description="Test",
            destination="Mountains",
            trip_date=datetime.now() + timedelta(days=1),
            difficulty=TripDifficulty.EASY,
            max_participants=5,
            leader_id=test_user_member.id,
        )
        db.session.add(trip)
        db.session.commit()

        report = TripReport(
            title="Photo Report",
            content="Test",
            trip_id=trip.id,
            author_id=test_user_member.id,
            is_published=True,
        )
        db.session.add(report)
        db.session.commit()

        photo = Photo(
            trip_report_id=report.id,
            filename="test.jpg",
            s3_key="photos/test.jpg",
            s3_bucket="test-bucket",
            uploaded_by=test_user_member.id,
            caption="Test photo",
        )
        db.session.add(photo)
        db.session.commit()

        response = client.get(url_for("reports.view_report", report_id=report.id))
        assert response.status_code == 200

        # Photo links should not open in new tab
        assert b'target="_blank"' not in response.data
        assert b'class="photo-link"' in response.data

    def test_photo_metadata_displayed(self, client, test_user_member):
        """Test that photo metadata is properly rendered for lightbox"""
        trip = Trip(
            title="Metadata Test Trip",
            description="Test",
            destination="Peak",
            trip_date=datetime.now() + timedelta(days=2),
            difficulty=TripDifficulty.DIFFICULT,
            max_participants=8,
            leader_id=test_user_member.id,
        )
        db.session.add(trip)
        db.session.commit()

        report = TripReport(
            title="Metadata Report",
            content="Content",
            trip_id=trip.id,
            author_id=test_user_member.id,
            is_published=True,
        )
        db.session.add(report)
        db.session.commit()

        photo = Photo(
            trip_report_id=report.id,
            filename="meta.jpg",
            s3_key="photos/meta.jpg",
            s3_bucket="test-bucket",
            uploaded_by=test_user_member.id,
            caption="Sunrise at 2500m",
            width=3840,
            height=2160,
            file_size=2048000,  # 2MB
        )
        db.session.add(photo)
        db.session.commit()

        response = client.get(url_for("reports.view_report", report_id=report.id))
        assert response.status_code == 200

        # Check metadata is in HTML for lightbox to use
        assert b"Sunrise at 2500m" in response.data
        assert b"3840" in response.data
        assert b"2160" in response.data
        assert b"2.0 MB" in response.data

    def test_multiple_photos_gallery(self, client, test_user_member):
        """Test that multiple photos are properly set up for gallery navigation"""
        trip = Trip(
            title="Gallery Trip",
            description="Multi-photo trip",
            destination="Alps",
            trip_date=datetime.now() + timedelta(days=3),
            difficulty=TripDifficulty.EXPERT,
            max_participants=6,
            leader_id=test_user_member.id,
        )
        db.session.add(trip)
        db.session.commit()

        report = TripReport(
            title="Gallery Report",
            content="Multiple photos",
            trip_id=trip.id,
            author_id=test_user_member.id,
            is_published=True,
        )
        db.session.add(report)
        db.session.commit()

        # Add multiple photos
        for i in range(5):
            photo = Photo(
                trip_report_id=report.id,
                filename=f"photo{i}.jpg",
                s3_key=f"photos/photo{i}.jpg",
                s3_bucket="test-bucket",
                uploaded_by=test_user_member.id,
                caption=f"Photo {i+1} of the journey",
                width=1920,
                height=1080,
            )
            db.session.add(photo)
        db.session.commit()

        response = client.get(url_for("reports.view_report", report_id=report.id))
        assert response.status_code == 200

        # Check gallery setup
        assert b'data-photo-count="5"' in response.data
        assert response.data.count(b'class="photo-link"') == 5
        assert response.data.count(b'class="photo-tile"') == 5

    def test_report_without_photos(self, client, test_user_member):
        """Test that reports without photos don't break lightbox initialization"""
        trip = Trip(
            title="No Photo Trip",
            description="Trip without photos",
            destination="Local Hill",
            trip_date=datetime.now() + timedelta(days=1),
            difficulty=TripDifficulty.EASY,
            max_participants=20,
            leader_id=test_user_member.id,
        )
        db.session.add(trip)
        db.session.commit()

        report = TripReport(
            title="Text Only Report",
            content="This report has no photos, just text.",
            trip_id=trip.id,
            author_id=test_user_member.id,
            is_published=True,
        )
        db.session.add(report)
        db.session.commit()

        response = client.get(url_for("reports.view_report", report_id=report.id))
        assert response.status_code == 200

        # Should still load lightbox scripts (for potential future photos)
        assert b"lightbox.js" in response.data
        # But no actual photos in gallery (data-photo-count="0" or no photos in mosaic)
        assert (
            b'data-photo-count="0"' in response.data or b'class="photo-tile"' not in response.data
        )

    def test_photo_accessibility_attributes(self, client, test_user_member):
        """Test that photos have proper accessibility attributes for lightbox"""
        trip = Trip(
            title="Accessible Trip",
            description="Testing accessibility",
            destination="Inclusive Peak",
            trip_date=datetime.now() + timedelta(days=5),
            difficulty=TripDifficulty.MODERATE,
            max_participants=12,
            leader_id=test_user_member.id,
        )
        db.session.add(trip)
        db.session.commit()

        report = TripReport(
            title="Accessible Report",
            content="Accessibility matters",
            trip_id=trip.id,
            author_id=test_user_member.id,
            is_published=True,
        )
        db.session.add(report)
        db.session.commit()

        photo = Photo(
            trip_report_id=report.id,
            filename="accessible.jpg",
            s3_key="photos/accessible.jpg",
            s3_bucket="test-bucket",
            uploaded_by=test_user_member.id,
            caption="Beautiful mountain vista with snow-capped peaks",
        )
        db.session.add(photo)
        db.session.commit()

        response = client.get(url_for("reports.view_report", report_id=report.id))
        assert response.status_code == 200

        # Check for alt text
        assert (
            b'alt="Beautiful mountain vista with snow-capped peaks"' in response.data
            or b'alt="Fotografija izleta"' in response.data
        )

        # Check for lazy loading
        assert b'loading="lazy"' in response.data

    def test_photo_error_handling(self, client, test_user_member):
        """Test that broken photo URLs are handled gracefully"""
        trip = Trip(
            title="Error Test Trip",
            description="Testing error handling",
            destination="Error Mountain",
            trip_date=datetime.now() + timedelta(days=1),
            difficulty=TripDifficulty.EASY,
            max_participants=10,
            leader_id=test_user_member.id,
        )
        db.session.add(trip)
        db.session.commit()

        report = TripReport(
            title="Error Handling Report",
            content="What if photos fail to load?",
            trip_id=trip.id,
            author_id=test_user_member.id,
            is_published=True,
        )
        db.session.add(report)
        db.session.commit()

        photo = Photo(
            trip_report_id=report.id,
            filename="404.jpg",
            s3_key="photos/404.jpg",
            s3_bucket="test-bucket",
            uploaded_by=test_user_member.id,
            caption="This photo will not load",
        )
        db.session.add(photo)
        db.session.commit()

        response = client.get(url_for("reports.view_report", report_id=report.id))
        assert response.status_code == 200

        # Should have error handling in place
        assert b"onerror=" in response.data
        assert b"photo-placeholder" in response.data


@pytest.mark.fast
class TestLightboxSecurity:
    """Test security aspects of lightbox implementation"""

    def test_xss_prevention_in_captions(self, client, test_user_member):
        """Test that photo captions are properly escaped"""
        trip = Trip(
            title="XSS Test Trip",
            description="Security test",
            destination="Secure Peak",
            trip_date=datetime.now() + timedelta(days=1),
            difficulty=TripDifficulty.MODERATE,
            max_participants=5,
            leader_id=test_user_member.id,
        )
        db.session.add(trip)
        db.session.commit()

        report = TripReport(
            title="Security Report",
            content="Testing XSS prevention",
            trip_id=trip.id,
            author_id=test_user_member.id,
            is_published=True,
        )
        db.session.add(report)
        db.session.commit()

        # Try to inject script via caption
        photo = Photo(
            trip_report_id=report.id,
            filename="safe.jpg",
            s3_key="photos/safe.jpg",
            s3_bucket="test-bucket",
            uploaded_by=test_user_member.id,
            caption="<script>alert('XSS')</script>Normal caption",
        )
        db.session.add(photo)
        db.session.commit()

        response = client.get(url_for("reports.view_report", report_id=report.id))
        assert response.status_code == 200

        # Script should be escaped
        assert b"<script>alert" not in response.data
        assert b"&lt;script&gt;" in response.data or b"Normal caption" in response.data

    def test_unauthorized_photo_access(self, client):
        """Test that lightbox respects report visibility permissions"""
        # Create admin user and unpublished report
        admin = User.create_user(email="lightbox_admin@test.com", name="Admin", password="password")
        admin.role = UserRole.ADMIN
        db.session.add(admin)
        db.session.commit()

        trip = Trip(
            title="Private Trip",
            description="Admin only",
            destination="Secret Peak",
            trip_date=datetime.now() + timedelta(days=1),
            difficulty=TripDifficulty.EASY,
            max_participants=3,
            leader_id=admin.id,
        )
        db.session.add(trip)
        db.session.commit()

        report = TripReport(
            title="Unpublished Report",
            content="Draft content",
            trip_id=trip.id,
            author_id=admin.id,
            is_published=False,  # Not published
        )
        db.session.add(report)
        db.session.commit()

        photo = Photo(
            trip_report_id=report.id,
            filename="private.jpg",
            s3_key="photos/private.jpg",
            s3_bucket="test-bucket",
            uploaded_by=admin.id,
            caption="Private photo",
        )
        db.session.add(photo)
        db.session.commit()

        # Try to access as anonymous user
        response = client.get(url_for("reports.view_report", report_id=report.id))
        assert response.status_code == 404  # Should not be accessible

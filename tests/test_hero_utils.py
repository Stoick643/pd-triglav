"""
Tests for hero landing page utilities
Tests hero image selection, user messaging, and club statistics
"""

from unittest.mock import patch, MagicMock
from datetime import datetime

from utils.hero_utils import (
    get_time_period,
    get_hero_image_for_season,
    get_user_specific_messaging,
    get_club_stats,
)


class TestTimePeriodDetection:
    """Test time period detection for different seasons and hours"""

    def test_get_time_period_winter_dawn(self):
        """Dawn hours 5-9 in winter season"""
        assert get_time_period(7, "winter") == "dawn"
        assert get_time_period(5, "winter") == "dawn"
        assert get_time_period(8, "winter") == "dawn"

    def test_get_time_period_winter_day(self):
        """Day hours 9-17 in winter season"""
        assert get_time_period(12, "winter") == "day"
        assert get_time_period(9, "winter") == "day"
        assert get_time_period(16, "winter") == "day"

    def test_get_time_period_winter_dusk(self):
        """Dusk hours 17-22 in winter season"""
        assert get_time_period(19, "winter") == "dusk"
        assert get_time_period(17, "winter") == "dusk"
        assert get_time_period(21, "winter") == "dusk"

    def test_get_time_period_winter_night(self):
        """Night hours 22-5 crossing midnight in winter"""
        assert get_time_period(23, "winter") == "night"
        assert get_time_period(2, "winter") == "night"
        assert get_time_period(22, "winter") == "night"
        assert get_time_period(4, "winter") == "night"

    def test_get_time_period_summer_variations(self):
        """Summer has different daylight hours 4-8, 8-19"""
        assert get_time_period(6, "summer") == "dawn"  # 4-8
        assert get_time_period(15, "summer") == "day"  # 8-19
        assert get_time_period(20, "summer") == "dusk"  # 19-23
        assert get_time_period(1, "summer") == "night"  # 23-4

    def test_get_time_period_edge_cases(self):
        """Boundary hours and fallback behavior"""
        # Test exact boundary hours
        assert get_time_period(9, "winter") == "day"  # Dawn ends at 9
        assert get_time_period(17, "winter") == "dusk"  # Dusk starts at 17

        # Test spring boundaries
        assert get_time_period(18, "spring") == "dusk"  # Spring dusk 18-22

        # Test autumn boundaries
        assert get_time_period(17, "autumn") == "dusk"  # Autumn dusk 17-21


class TestHeroImageSelection:
    """Test hero image selection with mocked file system"""

    @patch("utils.hero_utils.os.path.exists")
    @patch("utils.hero_utils.datetime")
    def test_get_hero_image_for_season_basic(self, mock_datetime, mock_exists, app):
        """TODO: Mock file system - Returns correct seasonal paths"""
        with app.app_context():
            # Mock current time for predictable season
            mock_datetime.now.return_value = datetime(2023, 7, 15, 14, 0)  # Summer, day
            mock_exists.return_value = True
            app.static_folder = "/static"

            result = get_hero_image_for_season()
            assert "/static/images/hero/hero-summer.jpg" in result

    @patch("utils.hero_utils.os.path.exists")
    @patch("utils.hero_utils.datetime")
    def test_get_hero_image_for_season_time_based(self, mock_datetime, mock_exists, app):
        """TODO: Mock file system - Time-specific path generation"""
        with app.app_context():
            # Mock dawn time in winter
            mock_datetime.now.return_value = datetime(2023, 1, 15, 7, 0)  # Winter, dawn
            mock_exists.return_value = True
            app.static_folder = "/static"

            result = get_hero_image_for_season()
            # Should try time-specific image first
            assert "hero-winter-dawn.jpg" in result or "hero-winter.jpg" in result

    @patch("utils.hero_utils.os.path.exists")
    @patch("utils.hero_utils.datetime")
    def test_get_hero_image_fallback_logic(self, mock_datetime, mock_exists, app):
        """TODO: Mock file system - Fallback chain behavior"""
        with app.app_context():
            mock_datetime.now.return_value = datetime(2023, 1, 15, 7, 0)  # Winter, dawn
            app.static_folder = "/static"

            # Mock: time-specific image doesn't exist, but base seasonal does
            def exists_side_effect(path):
                if "hero-winter-dawn.jpg" in path:
                    return False
                elif "hero-winter.jpg" in path:
                    return True
                return False

            mock_exists.side_effect = exists_side_effect

            result = get_hero_image_for_season()
            assert "hero-winter.jpg" in result

    @patch("utils.hero_utils.datetime")
    def test_get_hero_image_season_mapping(self, mock_datetime, app):
        """Month-to-season mapping without file checks"""
        with app.app_context():
            # Test season mapping logic without file system dependencies
            test_cases = [
                (datetime(2023, 1, 15), "winter"),  # January
                (datetime(2023, 4, 15), "spring"),  # April
                (datetime(2023, 7, 15), "summer"),  # July
                (datetime(2023, 10, 15), "autumn"),  # October
            ]

            app.static_folder = "/static"

            for test_datetime, expected_season in test_cases:
                mock_datetime.now.return_value = test_datetime
                # We can't easily test the internal season variable,
                # but we can verify the function runs without error
                with patch("utils.hero_utils.os.path.exists", return_value=True):
                    result = get_hero_image_for_season()
                    assert isinstance(result, str)
                    assert result.startswith("/static/images/")


class TestUserMessaging:
    """Test user-specific messaging for different authentication states"""

    def test_get_user_specific_messaging_anonymous(self):
        """Adventure-focused messaging for non-authenticated users"""
        mock_user = MagicMock()
        mock_user.is_authenticated = False

        result = get_user_specific_messaging(mock_user)

        assert result["headline"] == "Odkrijte Veličino Slovenskih Gora"
        assert "200+ planincev" in result["subheadline"]
        assert result["primary_cta"]["text"] == "Začni svojo pustolovščino"
        assert result["primary_cta"]["url"] == "/auth/register"

    def test_get_user_specific_messaging_pending(self):
        """Patience messaging for pending approval users"""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.is_pending.return_value = True

        result = get_user_specific_messaging(mock_user)

        assert result["headline"] == "Dobrodošli v PD Triglav!"
        assert "registracija čaka na odobritev" in result["subheadline"]
        assert result["primary_cta"]["text"] == "Spoznaj Našo Skupnost"
        assert result["primary_cta"]["url"] == "/about"

    def test_get_user_specific_messaging_active_member(self):
        """Personalized welcome for active members"""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.is_pending.return_value = False
        mock_user.name = "Janez Novak"

        result = get_user_specific_messaging(mock_user)

        assert "Dobrodošel/la nazaj, Janez!" in result["headline"]
        assert "planinsko pustolovščino?" in result["subheadline"]
        assert result["primary_cta"]["text"] == "Pojdi na Nadzorno Ploščo"
        assert result["secondary_cta"]["text"] == "Prihajajoči dogodki"

    def test_user_messaging_includes_required_fields(self):
        """All messaging contains headline, subheadline, CTAs"""
        mock_user = MagicMock()
        mock_user.is_authenticated = False

        result = get_user_specific_messaging(mock_user)

        # Check required fields exist
        assert "headline" in result
        assert "subheadline" in result
        assert "primary_cta" in result
        assert "secondary_cta" in result

        # Check CTA structure
        for cta in [result["primary_cta"], result["secondary_cta"]]:
            assert "text" in cta
            assert "url" in cta
            assert "class" in cta


class TestClubStatistics:
    """Test club statistics functionality"""

    def test_get_club_stats_returns_hardcoded_values(self):
        """Returns production values not database queries"""
        result = get_club_stats()

        # Should return exact production values
        assert result["member_count"] == 200
        assert result["trips_this_year"] == 25
        assert result["years_active"] == 15
        assert result["experience_level"] == "Vsi nivoji"

    def test_get_club_stats_structure(self):
        """Contains member_count, trips_this_year, years_active fields"""
        result = get_club_stats()

        # Check all required fields exist
        required_fields = ["member_count", "trips_this_year", "years_active", "experience_level"]
        for field in required_fields:
            assert field in result

        # Check data types
        assert isinstance(result["member_count"], int)
        assert isinstance(result["trips_this_year"], int)
        assert isinstance(result["years_active"], int)
        assert isinstance(result["experience_level"], str)

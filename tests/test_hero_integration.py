"""
Integration tests for hero landing page functionality
Tests route integration and template rendering
"""

from unittest.mock import patch
from flask import url_for


class TestHeroRouteIntegration:
    """Test hero functionality integration with Flask routes"""

    def test_index_route_includes_hero_data(self, client, app):
        """Index route provides hero messaging and stats"""
        with app.test_request_context():
            response = client.get(url_for("main.index"))

        assert response.status_code == 200
        html = response.get_data(as_text=True)

        # Check that hero section is present
        assert 'class="hero-section"' in html
        assert "hero-content" in html

    def test_index_route_different_user_states(self, client, app):
        """Different messaging for anonymous vs authenticated users"""
        with app.test_request_context():
            # Test anonymous user
            response = client.get(url_for("main.index"))
            html = response.get_data(as_text=True)

            # Should show registration-focused messaging
            assert "Odkrijte Veličino Slovenskih Gora" in html
            assert "Začni svojo pustolovščino" in html

    @patch("utils.hero_utils.get_hero_image_for_season")
    def test_index_route_hero_image_generation(self, mock_get_image, client, app):
        """Hero image URL generation works in routes"""
        mock_get_image.return_value = "/static/images/hero/hero-summer.jpg"

        with app.test_request_context():
            response = client.get(url_for("main.index"))

        # Verify the function was called
        mock_get_image.assert_called_once()

        # Check image appears in HTML
        html = response.get_data(as_text=True)
        assert "/static/images/hero/" in html


class TestHeroTemplateRendering:
    """Test hero template rendering with different data"""

    def test_hero_section_renders_correctly(self, client, app):
        """Hero HTML structure renders with data"""
        with app.test_request_context():
            response = client.get(url_for("main.index"))

        assert response.status_code == 200
        html = response.get_data(as_text=True)

        # Check hero structure elements
        assert '<section class="hero-section"' in html
        assert "hero-background" in html
        assert "hero-overlay" in html
        assert "hero-content" in html
        assert "hero-title" in html
        assert "hero-subtitle" in html
        assert "hero-stats" in html
        assert "hero-cta-buttons" in html

    def test_hero_statistics_display(self, client, app):
        """Club stats display correctly in template"""
        with app.test_request_context():
            response = client.get(url_for("main.index"))

        html = response.get_data(as_text=True)

        # Check hardcoded production statistics appear
        assert "200+" in html  # member count
        assert "25+" in html  # trips per year
        assert "15" in html  # years active
        assert "jubilejno leto" in html  # anniversary text
        assert "članov" in html
        assert "izletov letno" in html

    def test_hero_cta_buttons_render(self, client, app):
        """CTA buttons render with correct URLs/text"""
        with app.test_request_context():
            response = client.get(url_for("main.index"))

        html = response.get_data(as_text=True)

        # For anonymous users, should show registration CTA
        assert "Začni svojo pustolovščino" in html
        assert "/auth/register" in html

        # Secondary CTA should be present
        assert "btn-outline-light" in html


class TestHeroWithAuthenticatedUsers:
    """Test hero behavior with different authenticated user states"""

    def test_hero_with_pending_user(self, client, app, test_user_pending):
        """Hero shows appropriate messaging for pending users"""
        # Login the pending user using auth helper
        with app.test_request_context():
            response = client.post(
                "/auth/login", data={"email": test_user_pending.email, "password": "pendingpass"}
            )

            # Now check the hero page
            response = client.get(url_for("main.index"))

        html = response.get_data(as_text=True)

        # Should show pending approval messaging
        assert "Dobrodošli v PD Triglav!" in html
        assert "registracija čaka na odobritev" in html
        assert "Spoznaj Našo Skupnost" in html

    def test_hero_with_active_member(self, client, app, test_user_member):
        """Hero shows personalized welcome for active members"""
        # Login the member user using auth helper
        with app.test_request_context():
            response = client.post(
                "/auth/login", data={"email": test_user_member.email, "password": "memberpass"}
            )

            # Now check the hero page
            response = client.get(url_for("main.index"))

        html = response.get_data(as_text=True)

        # Should show personalized welcome
        assert "Dobrodošel/la nazaj" in html
        assert "planinsko pustolovščino?" in html
        assert "Prihajajoči dogodki" in html
        assert "/dashboard" in html


class TestHeroResponsiveness:
    """Test hero responsive behavior and mobile compatibility"""

    def test_hero_mobile_viewport_tags(self, client, app):
        """Hero includes proper mobile viewport and responsive tags"""
        with app.test_request_context():
            response = client.get(url_for("main.index"))

        html = response.get_data(as_text=True)

        # Check responsive meta tags
        assert 'name="viewport"' in html
        assert "width=device-width" in html

        # Check Bootstrap responsive classes
        assert "container-fluid" in html
        assert "col-12" in html
        assert "align-items-center" in html

    def test_hero_includes_javascript(self, client, app):
        """Hero page includes necessary JavaScript files"""
        with app.test_request_context():
            response = client.get(url_for("main.index"))

        html = response.get_data(as_text=True)

        # Check that hero.js is included
        assert "hero.js" in html

        # Check Bootstrap JS for responsive navigation
        assert "bootstrap" in html


class TestHeroSocialMediaTags:
    """Test Open Graph and social media meta tags"""

    def test_hero_includes_open_graph_tags(self, client, app):
        """Hero page includes Open Graph meta tags for social sharing"""
        with app.test_request_context():
            response = client.get(url_for("main.index"))

        html = response.get_data(as_text=True)

        # Check Open Graph tags
        assert 'property="og:type"' in html
        assert 'property="og:title"' in html
        assert 'property="og:description"' in html
        assert 'property="og:image"' in html

        # Check specific content
        assert "PD Triglav - pa ne samo na Triglav" in html
        assert "200+ planincev" in html
        assert "Triglav_OpenGraph.jpg" in html

    def test_hero_includes_twitter_card_tags(self, client, app):
        """Hero page includes Twitter Card meta tags"""
        with app.test_request_context():
            response = client.get(url_for("main.index"))

        html = response.get_data(as_text=True)

        # Check Twitter Card tags
        assert 'name="twitter:card"' in html
        assert 'name="twitter:title"' in html
        assert 'name="twitter:description"' in html
        assert 'name="twitter:image"' in html

        # Check card type
        assert "summary_large_image" in html

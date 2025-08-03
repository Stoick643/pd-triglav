"""
Hero landing page utilities for PD Triglav
Handles hero image selection, user messaging, and optimization
"""

import os
from datetime import datetime
from flask import current_app


def get_hero_image_for_season():
    """Returns seasonal and time-based hero image path with enhanced rotation system."""
    now = datetime.now()
    current_month = now.month
    current_hour = now.hour

    # Define seasonal mapping with time-based variations
    seasonal_images = {
        "winter": {
            "dawn": "hero/hero-winter-dawn.jpg",  # 5-9 AM
            "day": "hero/hero-winter.jpg",  # 9 AM - 5 PM
            "dusk": "hero/hero-winter-dusk.jpg",  # 5-10 PM
            "night": "hero/hero-winter-night.jpg",  # 10 PM - 5 AM
        },
        "spring": {
            "dawn": "hero/hero-primary-dawn.jpg",  # 5-9 AM
            "day": "hero/hero-primary.jpg",  # 9 AM - 6 PM
            "dusk": "hero/hero-primary-dusk.jpg",  # 6-10 PM
            "night": "hero/hero-primary-night.jpg",  # 10 PM - 5 AM
        },
        "summer": {
            "dawn": "hero/hero-summer-dawn.jpg",  # 4-8 AM
            "day": "hero/hero-summer.jpg",  # 8 AM - 7 PM
            "dusk": "hero/hero-summer-dusk.jpg",  # 7-11 PM
            "night": "hero/hero-summer-night.jpg",  # 11 PM - 4 AM
        },
        "autumn": {
            "dawn": "hero/hero-secondary-dawn.jpg",  # 6-9 AM
            "day": "hero/hero-secondary.jpg",  # 9 AM - 5 PM
            "dusk": "hero/hero-secondary-dusk.jpg",  # 5-9 PM
            "night": "hero/hero-secondary-night.jpg",  # 9 PM - 6 AM
        },
    }

    # Determine season based on month
    if current_month in [12, 1, 2]:
        season = "winter"
    elif current_month in [3, 4, 5]:
        season = "spring"
    elif current_month in [6, 7, 8]:
        season = "summer"
    else:  # 9, 10, 11
        season = "autumn"

    # Determine time period based on hour and season
    time_period = get_time_period(current_hour, season)

    # Get the time-specific image for the season
    season_images = seasonal_images[season]
    image_path = season_images.get(time_period, season_images["day"])

    # Verify image exists, fallback through time periods then to base seasonal image
    full_path = os.path.join(current_app.static_folder, "images", image_path)
    if not os.path.exists(full_path):
        current_app.logger.info(
            f"Time-specific hero image not found: {image_path}, trying base seasonal"
        )

        # Try the base seasonal image (day version)
        base_image = season_images["day"]
        base_path = os.path.join(current_app.static_folder, "images", base_image)

        if os.path.exists(base_path):
            image_path = base_image
        else:
            current_app.logger.warning(
                f"Base seasonal hero image not found: {base_image}, using primary fallback"
            )
            image_path = "hero/hero-primary.jpg"

    return f"/static/images/{image_path}"


def get_user_specific_messaging(user):
    """Generates personalized hero headline and CTA text based on user authentication state."""

    if not user.is_authenticated:
        # Non-authenticated users - focus on adventure and joining
        return {
            "headline": "Odkrijte Veličino Slovenskih Gora",
            "subheadline": "Pridružite se skupnosti 200+ planincev pri raziskovanju naših najlepših vrhov",
            "primary_cta": {
                "text": "Začni svojo pustolovščino",
                "url": "/auth/register",
                "class": "btn-primary",
            },
            "secondary_cta": {
                "text": "Oglej si naše izlete",
                "url": "/about",
                "class": "btn-outline-light",
            },
        }

    elif user.is_pending():
        # Pending users - encourage patience, show value
        return {
            "headline": "Dobrodošli v PD Triglav!",
            "subheadline": "Vaša registracija čaka na odobritev. Medtem si oglejte našo skupnost in aktivnosti.",
            "primary_cta": {
                "text": "Spoznaj Našo Skupnost",
                "url": "/about",
                "class": "btn-primary",
            },
            "secondary_cta": {
                "text": "Oglej Zgodovinske Dogodke",
                "url": "#history-section",
                "class": "btn-outline-light",
            },
        }

    else:
        # Active members - personalized welcome
        return {
            "headline": f"Dobrodošel/la nazaj, {user.name.split()[0]}!",
            "subheadline": "Pripravljeni na naslednjo planinsko pustolovščino?",
            "primary_cta": {
                "text": "Pojdi na Nadzorno Ploščo",
                "url": "/dashboard",
                "class": "btn-primary",
            },
            "secondary_cta": {
                "text": "Prihajajoči dogodki",
                "url": "/trips",
                "class": "btn-outline-light",
            },
        }


def get_time_period(hour, season):
    """Determines time period (dawn/day/dusk/night) based on hour and season."""
    # Seasonal time boundaries - daylight hours vary by season
    time_boundaries = {
        "winter": {"dawn": (5, 9), "day": (9, 17), "dusk": (17, 22), "night": (22, 5)},
        "spring": {"dawn": (5, 9), "day": (9, 18), "dusk": (18, 22), "night": (22, 5)},
        "summer": {"dawn": (4, 8), "day": (8, 19), "dusk": (19, 23), "night": (23, 4)},
        "autumn": {"dawn": (6, 9), "day": (9, 17), "dusk": (17, 21), "night": (21, 6)},
    }

    boundaries = time_boundaries[season]

    # Check each time period
    for period, (start, end) in boundaries.items():
        if period == "night":
            # Night spans midnight (e.g., 22-5 means 22:00-23:59 and 00:00-04:59)
            if start > end:  # Crosses midnight
                if hour >= start or hour < end:
                    return "night"
            else:  # Doesn't cross midnight (shouldn't happen for night, but safety)
                if start <= hour < end:
                    return "night"
        else:
            # Regular time periods
            if start <= hour < end:
                return period

    # Default fallback
    return "day"


def get_club_stats():
    """Returns actual production club statistics for social proof."""
    # Return actual production values instead of dev/test database queries
    return {
        "member_count": 200,
        "trips_this_year": 25,
        "years_active": 15,
        "experience_level": "Vsi nivoji",
    }


def optimize_hero_images():
    """Processes uploaded images into multiple sizes and WebP formats for performance."""
    # This is a placeholder for future image optimization
    # Would integrate with PIL/Pillow to create multiple sizes and WebP versions

    try:
        from PIL import Image
        import os

        hero_dir = os.path.join(current_app.static_folder, "images", "hero")

        # Image sizes for responsive design
        sizes = {
            "mobile": (768, 1024),  # Portrait mobile
            "tablet": (1024, 768),  # Landscape tablet
            "desktop": (1920, 1080),  # Desktop
            "xl": (2560, 1440),  # Large desktop
        }

        # Process each hero image
        for filename in os.listdir(hero_dir):
            if filename.endswith(".jpg"):
                base_name = filename.rsplit(".", 1)[0]
                img_path = os.path.join(hero_dir, filename)

                try:
                    with Image.open(img_path) as img:
                        # Create different sizes
                        for size_name, (width, height) in sizes.items():
                            # Resize maintaining aspect ratio
                            img_resized = img.copy()
                            img_resized.thumbnail((width, height), Image.Resampling.LANCZOS)

                            # Save as JPEG
                            jpg_path = os.path.join(hero_dir, f"{base_name}-{size_name}.jpg")
                            img_resized.save(jpg_path, "JPEG", quality=85, optimize=True)

                            # Save as WebP for modern browsers
                            webp_path = os.path.join(hero_dir, f"{base_name}-{size_name}.webp")
                            img_resized.save(webp_path, "WebP", quality=80, optimize=True)

                except Exception as e:
                    current_app.logger.error(f"Error optimizing image {filename}: {e}")

        return True

    except ImportError:
        current_app.logger.warning("PIL/Pillow not available for image optimization")
        return False
    except Exception as e:
        current_app.logger.error(f"Error in image optimization: {e}")
        return False

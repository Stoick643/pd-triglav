"""
Hero landing page utilities for PD Triglav
Handles hero image selection, user messaging, and optimization
"""

import os
from datetime import datetime
from flask import current_app


def get_hero_image_for_season():
    """Returns randomly selected hero image that changes every hour."""
    import random

    now = datetime.now()
    current_hour = now.hour

    # Get all hero images from the hero directory
    hero_dir = os.path.join(current_app.static_folder, "images", "hero")

    try:
        # Get all image files in hero directory
        if os.path.exists(hero_dir):
            all_files = os.listdir(hero_dir)
            hero_images = [
                f for f in all_files if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
            ]

            if hero_images:
                # Use hour as seed for consistent hourly rotation
                # This ensures same image is shown for the entire hour
                random.seed(current_hour)
                selected_image = random.choice(hero_images)
                image_path = f"hero/{selected_image}"

                current_app.logger.info(
                    f"Selected hero image for hour {current_hour}: {selected_image}"
                )
                return f"/static/images/{image_path}"
            else:
                current_app.logger.warning("No hero images found in hero directory")
        else:
            current_app.logger.warning("Hero directory does not exist")

    except Exception as e:
        current_app.logger.error(f"Error selecting hero image: {e}")

    # Fallback to primary hero image
    fallback_path = "hero/hero-primary.jpg"
    fallback_full_path = os.path.join(current_app.static_folder, "images", fallback_path)

    if os.path.exists(fallback_full_path):
        return f"/static/images/{fallback_path}"
    else:
        current_app.logger.error("Even fallback hero image not found")
        return "/static/images/hero/hero-primary.jpg"  # Return path anyway as last resort


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

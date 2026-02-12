import requests
import time
import json
import re
import random
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple


class EventParser:
    """
    Parses HTML content of a historical event page to extract structured data.
    """

    def __init__(self, soup: BeautifulSoup, url: str):
        self.soup = soup
        self.url = url
        self.full_text = self._get_full_text()

    def parse(self) -> Optional[Dict]:
        """
        Orchestrates the parsing of the event page.
        """
        title_element = self.soup.find('h1', class_='entry-title')
        if not self.soup.find('div', class_='entry-content') or not title_element:
            return None

        raw_title = title_element.get_text().strip()
        
        # Core data extraction
        extracted_date = self._extract_date()
        primary_year = self._extract_year()
        
        if not primary_year or not extracted_date:
            print(f"  ! Skipping event without year or date: {raw_title}")
            return None

        description, paragraphs = self._extract_description_and_paragraphs()
        
        # Entity extraction
        people = self._extract_people(paragraphs)
        location = self._extract_location(paragraphs)
        
        # Title refinement
        final_title = self._get_final_title(raw_title, paragraphs)

        # Determine category from content
        category = self._determine_category(final_title, description)

        return {
            "date": extracted_date, # Renamed from day_of_year to date
            "year": primary_year,
            "title": final_title,
            "description": description, # Renamed from description_sl to description, removed description_en
            "location": location,
            "people": people,
            "url": self.url, # Renamed from source_url to url
            "source_name": "zsa.si", # Kept for potential future use or logging
            "url_secondary": None, # Added
            "category": category, # Determined from content
            "methodology": None, # Added
            "url_methodology": None, # Added
            "is_featured": False, # Added
            "is_generated": True, # Added, matching model default
        }

    def _get_full_text(self) -> str:
        """Extracts all text from the main content area."""
        content_div = self.soup.find('div', class_='entry-content')
        return content_div.get_text().strip() if content_div else ""

    def _extract_date(self) -> Optional[str]:
        """Extracts the event date (MM-DD) from various parts of the page."""
        # Look in metadata area first
        date_text = self._get_metadata_text()
        
        # Slovenian month mappings
        month_mapping = {
            'januar': '01', 'januarja': '01', 'januarju': '01', 'jan': '01',
            'februar': '02', 'februarja': '02', 'februarju': '02', 'feb': '02',
            'marec': '03', 'marca': '03', 'marcu': '03', 'mar': '03',
            'april': '04', 'aprila': '04', 'aprilu': '04', 'apr': '04',
            'maj': '05', 'maja': '05', 'maju': '05',
            'junij': '06', 'junija': '06', 'juniju': '06', 'jun': '06',
            'julij': '07', 'julija': '07', 'juliju': '07', 'jul': '07',
            'avgust': '08', 'avgusta': '08', 'avgustu': '08', 'avg': '08',
            'september': '09', 'septembra': '09', 'septembru': '09', 'sep': '09',
            'oktober': '10', 'oktobra': '10', 'oktobru': '10', 'okt': '10',
            'november': '11', 'novembra': '11', 'novembru': '11', 'nov': '11',
            'december': '12', 'decembra': '12', 'decembru': '12', 'dec': '12'
        }
        
        # New reverse mapping for output
        output_month_names = { # Slovenian month names
            '01': 'Januar', '02': 'Februar', '03': 'Marec', '04': 'April',
            '05': 'Maj', '06': 'Junij', '07': 'Julij', '08': 'Avgust',
            '09': 'September', '10': 'Oktober', '11': 'November', '12': 'December'
        }
        
        # Date patterns: day first (Slovenian), then month first (English)
        patterns = [
            (r'\b(\d{1,2})\.\s*([a-zčšžđć]{3,9})\b', True),
            (r'\b(\d{1,2})\s+([a-zčšžđć]{3,9})\b', True),
            (r'\b([a-zčšžđć]{3,9})\s+(\d{1,2}),?\s*(?:\d{4})?\b', False) # Added 'čšžđć' to month name pattern
        ]

        for pattern, day_first in patterns:
            matches = re.findall(pattern, date_text.lower())
            for match in matches:
                # Ensure month_name_sl is always the full name for lookup
                day_str, month_name_sl_raw = match if day_first else (match[1], match[0])
                month_name_sl = None

                # Find the normalized month name if present in month_mapping keys
                for k, v in month_mapping.items():
                    if k.startswith(month_name_sl_raw):
                        month_name_sl = k
                        break
                
                if month_name_sl is None: continue # Skip if no matching month found

                month_mm = month_mapping.get(month_name_sl)
                if month_mm:
                    return f"{output_month_names[month_mm]} {day_str.lstrip('0')}" # Remove leading zero from day
        
        return None

    def _get_metadata_text(self) -> str:
        """Gathers text from typical metadata sections near the title."""
        title_element = self.soup.find('h1', class_='entry-title')
        if not title_element:
            return ""

        metadata_text = ""
        for selector in ['.entry-meta', '.post-meta', '.entry-date', '.published', 'time']:
            meta_element = self.soup.select_one(selector)
            if meta_element:
                metadata_text += " " + meta_element.get_text()

        if not metadata_text.strip():
            next_element = title_element.next_sibling
            chars_collected = 0
            while next_element and chars_collected < 300:
                if hasattr(next_element, 'get_text'):
                    text = next_element.get_text().strip()
                    metadata_text += " " + text
                    chars_collected += len(text)
                next_element = next_element.next_sibling
        
        return metadata_text if metadata_text.strip() else self.full_text

    def _extract_year(self) -> Optional[str]:
        """Finds the most likely primary year of the event."""
        all_years = re.findall(r'\b(1[89]\d{2}|20\d{2})\b', self.full_text)
        return all_years[0] if all_years else None

    def _determine_category(self, title: str, description: str) -> str:
        """Determines event category from title and description keywords."""
        text = (title + " " + description).lower()

        # Priority order for category detection
        if any(word in text for word in ['nesreča', 'nesreče', 'smrt', 'smrti', 'padec', 'padcu', 'umrl', 'umrla', 'tragedij', 'pogumni']):
            return "tragedy"
        elif any(word in text for word in ['prva', 'prvi vzpon', 'prvič', 'prvenstvena', 'prvenstveni', 'osvojil', 'osvojila', 'osvojitev']):
            return "first_ascent"
        elif any(word in text for word in ['odkritje', 'odkril', 'odkrila', 'raziskoval', 'raziskovala', 'raziskovanje']):
            return "discovery"
        elif any(word in text for word in ['odprava', 'ekspedicija', 'himalaj', 'himalaji', 'karakorum', 'andi']):
            return "expedition"
        else:
            return "achievement"  # Default fallback

    def _extract_description_and_paragraphs(self) -> Tuple[str, List[str]]:
        """Extracts and cleans the main description text."""
        paragraphs = [p.strip() for p in self.full_text.split('\n') if p.strip() and len(p) > 20]
        
        # Filter out common metadata or navigation lines
        clean_paragraphs = [
            p for p in paragraphs 
            if not any(skip in p.lower() for skip in ['kategorije', 'objavljeno', 'avtor', 'preberi'])
        ]
        
        description = ' '.join(clean_paragraphs[:3])
        if len(description) > 800:
            description = description[:800] + '...'
            
        return description, clean_paragraphs

    def _extract_people(self, paragraphs: List[str]) -> List[str]:
        """Extracts names of people from the text."""
        people = []
        # Slovenian name pattern: Capitalized First Name + Capitalized Last Name
        name_pattern = r'\b[A-ZČŠŽ][a-zčšžđć]+\s+[A-ZČŠŽ][a-zčšžđć]+\b'

        # Comprehensive false positives filter
        false_positives = {
            # Mountains and peaks
            'Broad Peak', 'El Capitan', 'Muztagh Tower', 'Muztagh Towerja', 'Half Dome',
            'Pik Komunizma', 'Mount Everest', 'Grandes Jorasses', 'Kriški Pod',
            'Bavškega Grintovca', 'Velika Planina', 'Stara Fužina', 'Za Akom',
            # Organizations
            'Gimnaziji Kranj', 'National Geographic', 'Poljski Plezalci', 'The Alpine',
            'Revija Alpinist', 'Indijski Himalaji', 'Nova Gorica', 'Raziskovalni postaji',
            # Places
            'Kamniška Bistrica', 'Dolgi Nemški', 'Zajedi Šit', 'Maria Anna',
            # Other
            'Akademskega alpinističnega'
        }

        for paragraph in paragraphs:
            names = re.findall(name_pattern, paragraph)
            for name in names:
                # Filter out false positives and names with genitive endings
                if (name not in false_positives and
                    not name.endswith('ja') and  # Genitive endings often not actual names
                    not name.endswith('ju') and
                    len(name.split()[0]) > 2):  # Filter very short first names
                    people.append(name)

        return list(set(people))[:5]

    def _extract_location(self, paragraphs: List[str]) -> Optional[str]:
        """Extracts the primary location from the text."""
        for paragraph in paragraphs:
            # Look for prepositions followed by a capitalized location name
            # More restrictive pattern to avoid capturing full sentences
            match = re.search(r'(?:v|na|pri|ob)\s+([A-ZČŠŽ][A-Za-zčšžđć]+(?:\s+[A-ZČŠŽ][A-Za-zčšžđć]+)?)', paragraph)
            if match:
                location = match.group(1).strip()
                # Filter out common false positives
                location_blacklist = {'AK Ravne', 'Indijski Himalaji', 'Raziskovalni postaji'}
                # Only accept locations with 1-2 words
                words = location.split()
                if (len(words) <= 2 and
                    location not in location_blacklist and
                    not any(word in location for word in ['med', 'prvi', 'sicer', 'leto'])):
                    return location
        return None

    def _get_final_title(self, raw_title: str, paragraphs: List[str]) -> str:
        """Determines the best title from available text."""
        
        def clean_title(title: str) -> str:
            # Remove dates, years, and metadata indicators
            title = re.sub(r'\b\d{1,2}\.\s*[a-zčšžđć]+\b', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\b[a-z]{3}\s+\d{1,2},?\s*\d{4}?\b', '', title, flags=re.IGNORECASE)
            title = re.sub(r'^\d{4}[:\-\s]+', '', title)
            title = re.sub(r'\s*[-–—]\s*(rojen|umrl|na današnji dan).*$', '', title, flags=re.IGNORECASE)
            return title.strip(' -–—').strip()

        cleaned_h1 = clean_title(raw_title)
        if len(cleaned_h1) > 15 and 'na današnji dan' not in cleaned_h1.lower():
            return cleaned_h1

        # Fallback: try to find a title-like sentence in the first paragraph
        if paragraphs:
            first_sentence = paragraphs[0].split('.')[0]
            if len(first_sentence) > 15 and len(first_sentence) < 120:
                return first_sentence

        return raw_title # Last resort


class HistoryScraper:
    """
    Scrapes historical event data from a website.
    """
    BASE_URL = 'https://www.zsa.si/category/na-danasnji-dan/'
    HEADERS = {
        'User-Agent': 'PDTriglav-HistoryScraper/1.1 (https://github.com/Stoick643/pd-triglav)'
    }

    def __init__(self, output_file: str = 'scraped_history.json'):
        self.output_file = output_file
        self.existing_urls = self._load_existing_urls()

    def _load_existing_urls(self) -> set:
        """Loads URLs from the existing JSON file to avoid re-scraping."""
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {event['url'] for event in data.get('events', [])}
        except (FileNotFoundError, json.JSONDecodeError):
            return set()

    def _save_data(self, new_events: List[Dict]):
        """Saves new events to the JSON file, merging with existing data."""
        all_data = {"events": []}
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass # File doesn't exist or is empty, start fresh

        # Ensure 'events' key exists and is a list
        if "events" not in all_data or not isinstance(all_data["events"], list):
            all_data["events"] = []

        all_data["events"].extend(new_events)

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(new_events)} new events to {self.output_file}")

    def get_all_event_urls(self) -> List[str]:
        """Crawls through category pages to find all individual event URLs."""
        all_urls = []
        page_url: Optional[str] = self.BASE_URL
        page_num = 1

        while page_url:
            print(f"Fetching URL list from: {page_url}")
            try:
                response = requests.get(page_url, headers=self.HEADERS, timeout=15)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"  ! Failed to fetch page list: {e}")
                break

            soup = BeautifulSoup(response.content, 'html.parser')

            urls_this_page = 0
            for header in soup.find_all('h2', class_='entry-title'):
                link = header.find('a')
                if link and link.has_attr('href'):
                    all_urls.append(link['href'])
                    urls_this_page += 1

            print(f"  Found {urls_this_page} URLs on page {page_num} (total: {len(all_urls)})")

            # Find pagination link - look for link containing "Older Entries"
            next_page_link = soup.find('a', string=lambda text: text and 'Older Entries' in text)
            page_url = next_page_link['href'] if next_page_link else None
            page_num += 1
            time.sleep(random.uniform(4, 6))  # Random 4-6s delay

        return all_urls

    def scrape_event_details(self, event_url: str, max_retries: int = 3) -> Optional[Dict]:
        """Scrapes details from a single event page with retry logic."""
        print(f"  > Scraping: {event_url}")
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = 2 ** attempt
                    print(f"  ! Retry {attempt + 1}/{max_retries}, waiting {delay}s...")
                    time.sleep(delay)
                
                response = requests.get(event_url, headers=self.HEADERS, timeout=20)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                parser = EventParser(soup, event_url)
                event_data = parser.parse()

                if event_data:
                    print(f"  [OK] Extracted: {event_data['date']} / {event_data['year']} - {event_data['title'][:50]}...")

                time.sleep(random.uniform(4, 6))  # Random 4-6s delay
                return event_data

            except requests.RequestException as e:
                print(f"  ! Error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    print(f"  ! Failed to scrape {event_url} after {max_retries} attempts.")
                    return None
        return None

    def run(self, limit: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """
        Main method to run the scraper, process new events, and save the data.
        Optionally filters events by a date range (MM-DD format).
        Returns the list of newly scraped events, or filtered events if a date range is provided.
        """
        print("Starting scraper...")
        all_urls = self.get_all_event_urls()
        
        new_urls = [url for url in all_urls if url not in self.existing_urls]
        print(f"\nFound {len(all_urls)} total URLs. {len(self.existing_urls)} existing, {len(new_urls)} new.")

        if limit is not None:
            print(f"Processing a maximum of {limit} new URLs.")
            new_urls = new_urls[:limit]

        if not new_urls:
            print("No new events to scrape. Exiting.")
            return []

        new_events = []
        failed_scrapes = 0
        
        for i, url in enumerate(new_urls, 1):
            print(f"\n[{i}/{len(new_urls)}] Processing URL...")
            try:
                details = self.scrape_event_details(url)
                if details:
                    new_events.append(details)
                else:
                    failed_scrapes += 1
            except Exception as e:
                failed_scrapes += 1
                print(f"  ! Unexpected error processing {url}: {e}")

        print("\n=== Scraping Summary ===")
        print(f"Successfully scraped: {len(new_events)}")
        print(f"Failed to scrape: {failed_scrapes}")

        if new_events:
            self._save_data(new_events) # Save all newly scraped events

        # Filter and report on events within the specified date range
        if start_date and end_date:
            from datetime import datetime

            # Slovenian month names for parsing
            month_map = {
                'Januar': 1, 'Februar': 2, 'Marec': 3, 'April': 4, 'Maj': 5, 'Junij': 6,
                'Julij': 7, 'Avgust': 8, 'September': 9, 'Oktober': 10, 'November': 11, 'December': 12
            }

            def parse_date_string(date_str):
                try:
                    month_name, day = date_str.split()
                    month = month_map[month_name]
                    # Use a fixed year for comparison, as we only care about month and day
                    return datetime(2000, month, int(day))
                except (ValueError, KeyError):
                    return None

            start_date_obj = parse_date_string(start_date)
            end_date_obj = parse_date_string(end_date)

            if not start_date_obj or not end_date_obj:
                print(f"\n--- Invalid date format for filtering: {start_date} to {end_date} ---")
                return new_events

            filtered_events = []
            for event in new_events:
                event_date_obj = parse_date_string(event.get('date', ''))
                if event_date_obj and start_date_obj <= event_date_obj <= end_date_obj:
                    filtered_events.append(event)

            print(f"\n--- Events matching date range {start_date} to {end_date} ---")
            if filtered_events:
                for event in filtered_events:
                    print(f"  - {event['date']} {event['year']}: {event['title']}")
            else:
                print("  No events found in the specified date range from the newly scraped batch.")
            
            return filtered_events # Return filtered events for further processing
        
        return new_events # Return all new events if no date filter applied


if __name__ == "__main__":
    # Set the date range for the rest of November
    start_date_str = "November 9"
    end_date_str = "November 30"

    scraper = HistoryScraper()
    # Scrape first 30 new articles (reduced to 30 for round 3 - conservative approach)
    # Using 5s delays to avoid rate limiting
    scraper.run(limit=30, start_date=start_date_str, end_date=end_date_str)

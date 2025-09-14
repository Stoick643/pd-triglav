import requests
import time
import json
from bs4 import BeautifulSoup

# Be a good web citizen: identify your script
HEADERS = {
    'User-Agent': 'SlovenianMountaineeringClub-HistoryBot/1.0 (info@example.com)'
}

def get_all_event_urls():
    """
    Crawls through the category pages to find all individual event URLs.
    """
    all_urls = []
    # The starting page
    page_url = 'https://www.zsa.si/category/na-danasnji-dan/'
    
    while page_url:
        print(f"Fetching URLs from: {page_url}")
        response = requests.get(page_url, headers=HEADERS)
        
        # Check if the request was successful
        if response.status_code != 200:
            print("Failed to fetch page.")
            break
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all event links on the current page
        # On this site, they are in h2 tags with class 'entry-title'
        for header in soup.find_all('h2', class_='entry-title'):
            link = header.find('a')
            if link and link.has_attr('href'):
                all_urls.append(link['href'])
                
        # Find the link to the next page
        next_page_link = soup.find('a', class_='next page-numbers')
        if next_page_link:
            page_url = next_page_link['href']
        else:
            page_url = None # No more pages
            
        time.sleep(2) # IMPORTANT: Pause for 2 seconds between page requests

    return all_urls

def extract_date_from_content(full_text):
    """
    Extract date from content text in various formats
    """
    import re
    
    # Slovenian month mappings
    month_mapping = {
        'januar': '01', 'januarja': '01',
        'februar': '02', 'februarja': '02', 
        'marec': '03', 'marca': '03',
        'april': '04', 'aprila': '04',
        'maj': '05', 'maja': '05',
        'junij': '06', 'junija': '06',
        'julij': '07', 'julija': '07',
        'avgust': '08', 'avgusta': '08',
        'september': '09', 'septembra': '09',
        'oktober': '10', 'oktobra': '10',
        'november': '11', 'novembra': '11',
        'december': '12', 'decembra': '12'
    }
    
    # English month mappings for dates like "Jun 25, 2025"
    english_months = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }
    
    # Try different date patterns
    date_patterns = [
        # English format: "Jun 25, 2025" or "Jun 25"
        (r'\b([A-Za-z]{3})\s+(\d{1,2}),?\s*(?:\d{4})?\b', english_months, False),
        # Slovenian format: "25. junij" or "25 junija"
        (r'\b(\d{1,2})\.\s*([a-zčšžđć]+)\b', month_mapping, True),
        (r'\b(\d{1,2})\s+([a-zčšžđć]+)\b', month_mapping, True),
    ]
    
    for pattern, month_dict, day_first in date_patterns:
        matches = re.findall(pattern, full_text.lower())
        
        for match in matches:
            if day_first:
                day, month_name = match
            else:
                month_name, day = match
            
            month_name = month_name.lower().strip()
            
            if month_name in month_dict:
                day = day.zfill(2)  # Pad with zero
                month = month_dict[month_name]
                return f"{month}-{day}"  # MM-DD format for better sorting
    
    return None

def clean_title(title_text):
    """
    Clean title text by removing date artifacts and metadata
    """
    import re
    
    # Remove common date patterns from titles
    cleaned = title_text
    
    # Remove dates like "24. avgust", "Jun 25", etc.
    cleaned = re.sub(r'\b\d{1,2}\.\s*[a-zčšžđć]+\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b[a-z]{3}\s+\d{1,2},?\s*\d{4}?\b', '', cleaned, flags=re.IGNORECASE)
    
    # Remove year prefixes like "1953: " or "1953 - "
    cleaned = re.sub(r'^\d{4}[:\-\s]+', '', cleaned)
    
    # Remove metadata indicators
    cleaned = re.sub(r'\s*[-–—]\s*(rojen|umrl|na današnji dan).*$', '', cleaned, flags=re.IGNORECASE)
    
    # Clean up extra whitespace and punctuation
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip(' -–—')
    
    return cleaned if cleaned else title_text

def extract_date_from_title_area(soup):
    """
    Extract date from metadata area immediately after title (first 300 chars)
    """
    import re
    
    # Look for content immediately after H1 title
    title_element = soup.find('h1', class_='entry-title')
    if not title_element:
        return None
    
    # Get text from elements that typically follow the title
    metadata_text = ""
    
    # Look for common metadata containers
    metadata_selectors = [
        '.entry-meta',
        '.post-meta', 
        '.entry-date',
        '.published',
        'time'
    ]
    
    for selector in metadata_selectors:
        meta_element = soup.select_one(selector)
        if meta_element:
            metadata_text += " " + meta_element.get_text()
    
    # If no specific metadata found, get text from next few siblings
    if not metadata_text.strip():
        next_element = title_element.next_sibling
        chars_collected = 0
        
        while next_element and chars_collected < 300:
            if hasattr(next_element, 'get_text'):
                text = next_element.get_text().strip()
                metadata_text += " " + text
                chars_collected += len(text)
            next_element = next_element.next_sibling
    
    # Enhanced month mappings including abbreviations
    month_mapping = {
        # Slovenian full names
        'januar': '01', 'januarja': '01', 'januarju': '01',
        'februar': '02', 'februarja': '02', 'februarju': '02', 
        'marec': '03', 'marca': '03', 'marcu': '03',
        'april': '04', 'aprila': '04', 'aprilu': '04',
        'maj': '05', 'maja': '05', 'maju': '05',
        'junij': '06', 'junija': '06', 'juniju': '06',
        'julij': '07', 'julija': '07', 'juliju': '07',
        'avgust': '08', 'avgusta': '08', 'avgustu': '08',
        'september': '09', 'septembra': '09', 'septembru': '09',
        'oktober': '10', 'oktobra': '10', 'oktobru': '10',
        'november': '11', 'novembra': '11', 'novembru': '11',
        'december': '12', 'decembra': '12', 'decembru': '12',
        
        # Common abbreviations
        'avg': '08', 'sep': '09', 'okt': '10', 'nov': '11', 'dec': '12',
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'maj': '05', 'jun': '06', 'jul': '07'
    }
    
    # English months
    english_months = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'june': '06', 'july': '07', 'august': '08', 'september': '09',
        'october': '10', 'november': '11', 'december': '12'
    }
    
    # Combine all month mappings
    all_months = {**month_mapping, **english_months}
    
    # Date patterns - return MM-DD format for better sorting
    date_patterns = [
        # WordPress style: "Avg 11, 2023" or "Aug 11"
        (r'\b([a-z]{3,9})\s+(\d{1,2}),?\s*(?:\d{4})?\b', all_months, False),
        # Slovenian: "11. avgust" or "11 avgusta"  
        (r'\b(\d{1,2})\.\s*([a-zčšžđć]{3,9})\b', all_months, True),
        (r'\b(\d{1,2})\s+([a-zčšžđć]{3,9})\b', all_months, True),
    ]
    
    for pattern, month_dict, day_first in date_patterns:
        matches = re.findall(pattern, metadata_text.lower())
        
        for match in matches:
            if day_first:
                day, month_name = match
            else:
                month_name, day = match
            
            month_name = month_name.lower().strip()
            
            if month_name in month_dict:
                day = day.zfill(2)
                month = month_dict[month_name]
                return f"{month}-{day}"  # MM-DD format for better sorting
    
    return None

def scrape_event_details(event_url, max_retries=3):
    """
    Scrapes the details (year, description) from a single event page with retry logic.
    """
    print(f"  > Scraping: {event_url}")
    
    for attempt in range(max_retries):
        try:
            # Add delay with exponential backoff
            if attempt > 0:
                delay = 2 ** attempt  # 2, 4, 8 seconds
                print(f"  ! Retry {attempt + 1}/{max_retries}, waiting {delay} seconds...")
                time.sleep(delay)
            
            response = requests.get(event_url, headers=HEADERS, timeout=15)
            
            if response.status_code != 200:
                print(f"  ! HTTP {response.status_code} for {event_url}")
                if attempt == max_retries - 1:
                    return None
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            break
            
        except (requests.exceptions.RequestException, ConnectionResetError, Exception) as e:
            print(f"  ! Error on attempt {attempt + 1}: {str(e)[:100]}...")
            if attempt == max_retries - 1:
                print(f"  ! Failed to scrape {event_url} after {max_retries} attempts")
                return None
            continue
    
    # The main content is in a div with this class
    content = soup.find('div', class_='entry-content')
    title_element = soup.find('h1', class_='entry-title')
    
    if not content or not title_element:
        return None
    
    # Get raw title text 
    title_text = title_element.get_text().strip()
    
    # Clean the H1 title (remove dates and metadata)
    cleaned_h1_title = clean_title(title_text)
    
    # Clean and extract text from content
    full_text = content.get_text().strip()
    
    # Extract date from title area first, then full content as fallback
    extracted_date = extract_date_from_title_area(soup) or extract_date_from_content(full_text)
    
    # Split into paragraphs and clean
    paragraphs = [p.strip() for p in full_text.split('\n') if p.strip()]
    paragraphs = [p for p in paragraphs if len(p) > 20]  # Filter very short lines
    
    # Find content for description
    description_parts = []
    content_event_title = None
    
    import re
    
    for paragraph in paragraphs:
        # Skip navigation elements and metadata
        if any(skip in paragraph.lower() for skip in ['kategorije', 'objavljeno', 'avtor', 'preberi']):
            continue
            
        # Look for year-prefixed events (fallback title extraction)
        year_event_match = re.match(r'^(\d{4})[:\-\s]+(.+)', paragraph)
        if year_event_match and not content_event_title:
            content_event_title = year_event_match.group(2).strip()
            description_parts.append(paragraph)
            continue
        
        # Add substantial paragraphs to description
        description_parts.append(paragraph)
    
    # Extract people names (Capitalized Name Surname patterns)
    people = []
    for paragraph in description_parts:
        # Find Slovenian name patterns
        names = re.findall(r'\b[A-ZČŠŽĐĆ][a-zčšžđć]+\s+[A-ZČŠŽĐĆ][a-zčšžđć]+\b', paragraph)
        people.extend(names)
    
    # Remove duplicates and limit
    people = list(set(people))[:5]
    
    # Find locations (look for "na/v/pri + Capitalized Location")
    locations = []
    for paragraph in description_parts:
        location_matches = re.findall(r'(?:na|v|pri)\s+([A-ZČŠŽĐĆ][A-Za-zčšžđć\s]+?)(?:[,.]|$)', paragraph)
        locations.extend(location_matches)
    
    location = locations[0].strip() if locations else None
    
    # Find years more reliably
    all_years = re.findall(r'\b(1[89]\d{2}|20\d{2})\b', full_text)
    primary_year = all_years[0] if all_years else None
    
    # Combine description parts (limit to 3 paragraphs for readability)
    clean_description = ' '.join(description_parts[:3])
    if len(clean_description) > 600:
        clean_description = clean_description[:600] + '...'
    
    # Determine best title (priority: cleaned H1 → content extraction → raw H1)
    final_title = None
    
    # Use cleaned H1 if it's substantial and not generic
    if len(cleaned_h1_title) > 10 and not any(generic in cleaned_h1_title.lower() 
                                             for generic in ['na današnji dan', 'rojen', 'umrl']):
        final_title = cleaned_h1_title
    # Otherwise use content-extracted title if available
    elif content_event_title:
        final_title = content_event_title
    # Fall back to first paragraph
    elif description_parts:
        final_title = description_parts[0][:100]
        if len(description_parts[0]) > 100:
            final_title += '...'
    # Last resort: use raw title
    else:
        final_title = title_text
    
    # Skip events without year
    if not primary_year:
        print(f"  ! Skipping event without year: {title_text}")
        return None
    
    # Skip events without date
    if not extracted_date:
        print(f"  ! Skipping event without date: {final_title}")
        return None
    
    event_data = {
        "day_of_year": extracted_date,  # No longer need "or unknown" since we skip events without dates
        "year": primary_year,
        "title": final_title,  # Use prioritized title
        "description_sl": clean_description,
        "description_en": "",
        "location": location,
        "people": people,
        "source_name": "zsa.si",
        "source_url": event_url
    }
    
    print(f"  ✓ Extracted: {extracted_date or 'No date'} / {primary_year} - {final_title[:50]}...")
    
    # Be polite to the server - longer delay between requests
    time.sleep(3)  # Increased from 1 to 3 seconds
    return event_data

# --- Main Script ---
if __name__ == "__main__":
    event_urls = get_all_event_urls()
    print(f"\nFound {len(event_urls)} event URLs to scrape.")
    
    all_events_data = []
    successful_scrapes = 0
    failed_scrapes = 0
    
    for i, url in enumerate(event_urls[:10], 1):
        print(f"\n[{i}/10] Processing URL {i} of 10...")
        try:
            details = scrape_event_details(url)
            if details:
                all_events_data.append(details)
                successful_scrapes += 1
            else:
                failed_scrapes += 1
                print(f"  ! No data extracted from {url}")
        except Exception as e:
            failed_scrapes += 1
            print(f"  ! Unexpected error processing {url}: {str(e)[:100]}...")
            continue
    
    print(f"\n=== Scraping Summary ===")
    print(f"Successful: {successful_scrapes}")
    print(f"Failed: {failed_scrapes}")
    print(f"Total events saved: {len(all_events_data)}")
            
    # Save the final data to a JSON file
    output_data = {"events": all_events_data}
    with open('scraped_history.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"\nSuccessfully scraped {len(all_events_data)} events and saved to scraped_history.json")
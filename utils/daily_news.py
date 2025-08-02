import datetime
import re
import time
import requests
from newsapi import NewsApiClient
from flask import current_app
import feedparser
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup


def get_daily_mountaineering_news_for_homepage():
    """Get daily news for homepage - uses database cache"""
    from models.content import DailyNews

    # Try to get cached news first
    cached_news = DailyNews.get_todays_news()
    if cached_news:
        return cached_news

    # If no cached news, fetch from API and cache it
    return fetch_and_cache_news()


def fetch_and_cache_news():
    """Fetch news using RSS feeds with NewsAPI fallback"""
    from models.content import DailyNews

    try:
        # Use new RSS-based news aggregator
        aggregator = ClimbingNewsAggregator()
        all_articles = aggregator.fetch_all_news()

        current_app.logger.info(f"RSS aggregator returned {len(all_articles)} articles")

        # Select top 3 articles with Slovenian content priority
        final_articles = []
        slovenian_count = 0
        max_articles = 3
        max_slovenian = 2

        for article in all_articles:
            if len(final_articles) >= max_articles:
                break

            # Check if this is Slovenian content
            content_lower = f"{article.get('title', '')} {article.get('summary', '')}".lower()
            is_slovenian = any(
                term in content_lower
                for term in ["slovenia", "slovenian", "janja garnbret", "luka lindič"]
            )

            if is_slovenian and slovenian_count < max_slovenian:
                final_articles.append(article)
                slovenian_count += 1
            elif not is_slovenian:
                final_articles.append(article)

        # Format for database caching (maintain existing format)
        summaries = []
        for article in final_articles:
            summaries.append(
                {
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "summary": article.get("summary", "No description available"),
                    "published_at": article.get("published_at", ""),
                    "language": article.get("language", "en"),
                    "source": article.get("source", "unknown"),
                    "source_name": article.get("source_name", ""),
                }
            )

        # Cache the results in database
        DailyNews.cache_todays_news(summaries)

        current_app.logger.info(f"Cached {len(summaries)} news articles")
        return summaries

    except Exception as e:
        current_app.logger.error(f"RSS news fetching failed: {e}")

        # Fallback to original NewsAPI-only approach
        return fetch_and_cache_news_fallback()


def fetch_and_cache_news_fallback():
    """Original NewsAPI-only implementation as fallback"""
    from models.content import DailyNews

    try:
        current_app.logger.info("Using NewsAPI fallback for news fetching")

        # Initialize NewsAPI client
        api_key = current_app.config.get("NEWS_API_KEY")
        if not api_key:
            current_app.logger.warning("No NEWS_API_KEY configured")
            return []

        newsapi = NewsApiClient(api_key=api_key)

        # Simplified search for fallback
        search_terms = ["rock climbing", "mountaineering", "alpine climbing"]
        all_articles = []

        end_time = datetime.datetime.utcnow()
        start_time = end_time - datetime.timedelta(days=7)
        from_date = start_time.strftime("%Y-%m-%d")

        for term in search_terms:
            try:
                response = newsapi.get_everything(
                    q=term, from_param=from_date, language="en", sort_by="relevancy", page_size=3
                )

                articles = response.get("articles", [])
                for article in articles:
                    formatted = {
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "summary": article.get("description", ""),
                        "published_at": article.get("publishedAt", ""),
                        "source": "newsapi",
                        "language": "en",
                    }
                    all_articles.append(formatted)

            except Exception as e:
                current_app.logger.warning(f"NewsAPI fallback error for '{term}': {e}")
                continue

        # Simple deduplication and selection
        unique_articles = {}
        for article in all_articles:
            if article["url"]:
                unique_articles[article["url"]] = article

        final_articles = list(unique_articles.values())[:3]

        # Cache results
        DailyNews.cache_todays_news(final_articles)

        current_app.logger.info(f"NewsAPI fallback cached {len(final_articles)} articles")
        return final_articles

    except Exception as e:
        current_app.logger.error(f"NewsAPI fallback also failed: {e}")
        return []


# This function would be called daily by your client's backend system.
# The `scheduler` tool in this environment is effectively doing something similar
# by triggering a specific prompt at a set interval.


class RSSFeedParser:
    """Parse RSS feeds from specialized climbing websites"""

    # Configuration of RSS sources with metadata
    RSS_SOURCES = {
        "planetmountain": {
            "url": "https://www.planetmountain.com/en/rss.xml",
            "name": "PlanetMountain",
            "credibility": 1.0,
            "language": "en",
        },
        "gripped": {
            "url": "https://gripped.com/feed/",
            "name": "Gripped Magazine",
            "credibility": 0.9,
            "language": "en",
        },
        "ukclimbing": {
            "url": "https://www.ukclimbing.com/news/rss",
            "name": "UK Climbing",
            "credibility": 0.85,
            "language": "en",
        },
        "8a": {
            "url": "https://www.8a.nu/rss/",
            "name": "8a.nu",
            "credibility": 0.8,
            "language": "en",
        },
    }

    def __init__(self):
        self.timeout = 10  # seconds

    def parse_feed(self, url, source_name=None):
        """Parse a single RSS feed and return formatted articles"""
        try:
            # Parse RSS feed with timeout
            feed = feedparser.parse(url)

            # Check for parse errors
            if hasattr(feed, "bozo") and feed.bozo:
                current_app.logger.warning(f"RSS parse warning for {url}: {feed.bozo_exception}")
                if not feed.entries:  # If completely broken, return empty
                    return []

            # Extract source name from URL if not provided
            if not source_name:
                source_name = self._extract_source_name(url)

            articles = []
            for entry in feed.entries:
                try:
                    # Get raw summary/description
                    raw_summary = entry.get("summary", entry.get("description", ""))

                    article = {
                        "title": entry.get("title", "").strip(),
                        "url": entry.get("link", ""),
                        "summary": self._clean_html_content(raw_summary),
                        "published_at": self._parse_date(entry),
                        "source": source_name,
                        "language": "en",  # Default to English for now
                    }

                    # Skip articles without essential data or meaningful content
                    if (
                        article["title"]
                        and article["url"]
                        and article["summary"]
                        and len(article["summary"]) > 20
                    ):
                        articles.append(article)

                except Exception as e:
                    current_app.logger.warning(f"Error parsing RSS entry from {url}: {e}")
                    continue

            current_app.logger.info(f"Parsed {len(articles)} articles from {source_name}")
            return articles

        except Exception as e:
            current_app.logger.error(f"Failed to parse RSS feed {url}: {e}")
            return []

    def fetch_all_feeds(self):
        """Fetch articles from all configured RSS sources"""
        all_articles = []

        for source_key, source_config in self.RSS_SOURCES.items():
            try:
                articles = self.parse_feed(source_config["url"], source_key)

                # Add source metadata to articles
                for article in articles:
                    article["source_credibility"] = source_config["credibility"]
                    article["source_name"] = source_config["name"]

                all_articles.extend(articles)

            except Exception as e:
                current_app.logger.error(f"Failed to fetch RSS from {source_key}: {e}")
                continue

        current_app.logger.info(f"Fetched total of {len(all_articles)} articles from RSS sources")
        return all_articles

    def _extract_source_name(self, url):
        """Extract a clean source name from RSS URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]

            # Extract main domain name
            source_name = domain.split(".")[0]

            # Handle special cases
            if "8a" in domain:
                return "8a"

            return source_name

        except Exception:
            return "unknown"

    def _parse_date(self, entry):
        """Parse RSS entry date to ISO format"""
        try:
            # Try different date fields that RSS feeds might use
            date_fields = ["published_parsed", "updated_parsed"]

            for field in date_fields:
                if hasattr(entry, field):
                    parsed_time = getattr(entry, field)
                    if parsed_time:
                        dt = datetime.datetime(*parsed_time[:6])
                        return dt.isoformat() + "Z"

            # Fallback to string parsing
            date_str = entry.get("published", entry.get("updated", ""))
            if date_str:
                # Try to parse common RSS date formats
                try:
                    dt = datetime.datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                    return dt.isoformat()
                except ValueError:
                    # If parsing fails, return current time
                    pass

            # Default to current time if no date found
            return datetime.datetime.utcnow().isoformat() + "Z"

        except Exception as e:
            current_app.logger.warning(f"Date parsing error: {e}")
            return datetime.datetime.utcnow().isoformat() + "Z"

    def _clean_html_content(self, html_text):
        """Clean HTML content and remove unwanted patterns"""
        if not html_text:
            return ""

        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_text, "html.parser")

            # Get plain text without HTML tags
            text = soup.get_text()

            # Remove common RSS footer patterns
            footer_patterns = [
                r"The post .+ appeared first on .+",
                r"Continue reading .+",
                r"Read more about .+",
                r"View this post on .+",
                r"Originally published on .+",
                r"Source: .+",
                r"\[.+\]$",  # Remove content in square brackets at end
            ]

            for pattern in footer_patterns:
                text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

            # Clean up whitespace and normalize text
            text = re.sub(r"\s+", " ", text)  # Replace multiple whitespace with single space
            text = text.strip()

            # Remove trailing periods and common sentence enders if they seem incomplete
            if text.endswith("...") or text.endswith("…."):
                text = text.rstrip(".… ")

            # Ensure reasonable length (truncate at sentence boundary if too long)
            if len(text) > 300:
                # Try to cut at sentence boundary
                sentences = text.split(". ")
                truncated = ""
                for sentence in sentences:
                    if len(truncated + sentence + ". ") <= 300:
                        truncated += sentence + ". "
                    else:
                        break

                if truncated:
                    text = truncated.strip()
                else:
                    # Fallback: cut at word boundary
                    words = text.split()[:50]  # Approximately 300 chars
                    text = " ".join(words)
                    if not text.endswith("."):
                        text += "..."

            return text

        except Exception as e:
            current_app.logger.warning(f"HTML cleaning error: {e}")
            # Fallback: basic HTML tag removal with regex
            text = re.sub(r"<[^>]+>", "", html_text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:300] + ("..." if len(text) > 300 else "")


class WebScrapingParser:
    """Parse articles from climbing websites using web scraping"""

    # Configuration for site-specific scraping
    SCRAPING_SOURCES = {
        "aac": {
            "url": "https://americanalpineclub.org/news",
            "name": "American Alpine Club",
            "selectors": {
                "articles": "article.news-item, .news-article, .post",
                "title": "h1, h2, h3, .title, .headline",
                "url": 'a[href*="/news/"], a[href*="/article/"], a.permalink',
                "summary": ".excerpt, .summary, p.lead, .description",
                "date": ".date, .publish-date, .posted-on, time",
            },
            "credibility": 0.95,
            "rate_limit": 2,  # seconds between requests
            "language": "en",
        },
        "climbing": {
            "url": "https://www.climbing.com/news/",
            "name": "Climbing Magazine",
            "selectors": {
                "articles": ".post, article, .news-item",
                "title": "h1, h2, .entry-title, .post-title",
                "url": 'a[href*="/news/"], .entry-title a, .post-title a',
                "summary": ".excerpt, .entry-summary, .post-excerpt, p",
                "date": ".date, .entry-date, .post-date, time",
            },
            "credibility": 0.9,
            "rate_limit": 2,
            "language": "en",
        },
        "explorersweb": {
            "url": "https://explorersweb.com/category/news/",
            "name": "Explorers Web",
            "selectors": {
                "articles": ".post, article, .news-post",
                "title": "h1, h2, .entry-title",
                "url": 'a[href*="/news/"], .entry-title a',
                "summary": ".entry-excerpt, .excerpt, p",
                "date": ".entry-date, .date, time",
            },
            "credibility": 0.85,
            "rate_limit": 3,
            "language": "en",
        },
    }

    def __init__(self):
        self.session = requests.Session()
        # Set a respectful user agent
        self.session.headers.update(
            {"User-Agent": "PD Triglav News Aggregator (contact: admin@pd-triglav.si)"}
        )
        self.timeout = 15  # seconds
        self.last_request_time = {}

    def scrape_site(self, source_key, source_config):
        """Scrape articles from a single site"""
        try:
            # Implement rate limiting
            self._apply_rate_limit(source_key, source_config["rate_limit"])

            # Fetch the page
            response = self.session.get(source_config["url"], timeout=self.timeout)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract articles using site-specific selectors
            articles = self._extract_articles(soup, source_config, source_key)

            current_app.logger.info(
                f"Scraped {len(articles)} articles from {source_config['name']}"
            )
            return articles

        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Failed to scrape {source_config['name']}: {e}")
            return []
        except Exception as e:
            current_app.logger.error(f"Error scraping {source_config['name']}: {e}")
            return []

    def _apply_rate_limit(self, source_key, rate_limit_seconds):
        """Apply rate limiting between requests to the same source"""
        current_time = time.time()

        if source_key in self.last_request_time:
            time_since_last = current_time - self.last_request_time[source_key]
            if time_since_last < rate_limit_seconds:
                sleep_time = rate_limit_seconds - time_since_last
                current_app.logger.debug(
                    f"Rate limiting: sleeping {sleep_time:.2f}s for {source_key}"
                )
                time.sleep(sleep_time)

        self.last_request_time[source_key] = time.time()

    def _extract_articles(self, soup, source_config, source_key):
        """Extract articles from parsed HTML using configured selectors"""
        articles = []
        selectors = source_config["selectors"]

        # Find all article containers
        article_elements = soup.select(selectors["articles"])

        for element in article_elements[:10]:  # Limit to first 10 articles
            try:
                article = self._extract_single_article(
                    element, selectors, source_config, source_key
                )
                if article:
                    articles.append(article)
            except Exception as e:
                current_app.logger.warning(
                    f"Error extracting article from {source_config['name']}: {e}"
                )
                continue

        return articles

    def _extract_single_article(self, element, selectors, source_config, source_key):
        """Extract data from a single article element"""
        # Extract title
        title_elem = element.select_one(selectors["title"])
        if not title_elem:
            return None
        title = title_elem.get_text().strip()

        # Extract URL
        url_elem = element.select_one(selectors["url"])
        if not url_elem:
            return None
        url = url_elem.get("href", "")

        # Make URL absolute if it's relative
        if url.startswith("/"):
            base_url = urlparse(source_config["url"])
            url = f"{base_url.scheme}://{base_url.netloc}{url}"
        elif not url.startswith("http"):
            url = urljoin(source_config["url"], url)

        # Extract summary
        summary_elem = element.select_one(selectors["summary"])
        raw_summary = summary_elem.get_text().strip() if summary_elem else ""

        # Clean HTML content using existing method
        # We'll need to access this from RSSFeedParser - let's create a shared method
        summary = self._clean_html_content(raw_summary)

        # Extract date
        date_elem = element.select_one(selectors["date"])
        published_at = (
            self._parse_date(date_elem)
            if date_elem
            else datetime.datetime.utcnow().isoformat() + "Z"
        )

        # Basic validation
        if not title or not url or len(summary) < 20:
            return None

        return {
            "title": title,
            "url": url,
            "summary": summary,
            "published_at": published_at,
            "source": source_key,
            "source_name": source_config["name"],
            "source_credibility": source_config["credibility"],
            "language": source_config.get("language", "en"),
            "source_type": "webscraping",
        }

    def _clean_html_content(self, html_text):
        """Clean HTML content - reuse RSSFeedParser method"""
        # For now, create a temporary RSSFeedParser to reuse the method
        # This is not ideal but ensures consistency
        temp_parser = RSSFeedParser()
        return temp_parser._clean_html_content(html_text)

    def _parse_date(self, date_elem):
        """Parse date from various formats"""
        try:
            if not date_elem:
                return datetime.datetime.utcnow().isoformat() + "Z"

            # Try to get datetime attribute first
            if date_elem.get("datetime"):
                date_str = date_elem.get("datetime")
            else:
                date_str = date_elem.get_text().strip()

            # Try various date parsing approaches
            try:
                # ISO format
                if "T" in date_str and ("Z" in date_str or "+" in date_str):
                    return date_str

                # Common formats
                for fmt in [
                    "%Y-%m-%d",
                    "%B %d, %Y",
                    "%b %d, %Y",
                    "%d %B %Y",
                    "%d %b %Y",
                    "%m/%d/%Y",
                    "%d/%m/%Y",
                ]:
                    try:
                        dt = datetime.datetime.strptime(date_str[:20], fmt)
                        return dt.isoformat() + "Z"
                    except ValueError:
                        continue

            except Exception:
                pass

            # Fallback to current time
            return datetime.datetime.utcnow().isoformat() + "Z"

        except Exception as e:
            current_app.logger.warning(f"Date parsing error: {e}")
            return datetime.datetime.utcnow().isoformat() + "Z"

    def fetch_all_sites(self):
        """Fetch articles from all configured scraping sources"""
        all_articles = []

        for source_key, source_config in self.SCRAPING_SOURCES.items():
            try:
                articles = self.scrape_site(source_key, source_config)

                # Add source metadata to articles
                for article in articles:
                    article["source_credibility"] = source_config["credibility"]
                    article["source_name"] = source_config["name"]

                all_articles.extend(articles)

            except Exception as e:
                current_app.logger.error(f"Failed to fetch from {source_key}: {e}")
                continue

        current_app.logger.info(f"Fetched total of {len(all_articles)} articles from web scraping")
        return all_articles


class ClimbingNewsAggregator:
    """Aggregate and score news from multiple sources"""

    def __init__(self):
        self.rss_parser = RSSFeedParser()
        self.web_scraper = WebScrapingParser()

    def fetch_all_news(self):
        """Fetch news from all sources (RSS + Web Scraping + NewsAPI fallback)"""
        # Start with RSS feeds
        rss_articles = self.rss_parser.fetch_all_feeds()

        # Add web scraping articles
        scraping_articles = self.web_scraper.fetch_all_sites()

        # Get NewsAPI articles as fallback
        newsapi_articles = self._fetch_newsapi_fallback()

        # Combine all three sources
        return self.combine_sources(rss_articles, scraping_articles, newsapi_articles)

    def combine_sources(self, rss_articles, scraping_articles, newsapi_articles):
        """Combine RSS, web scraping, and NewsAPI articles with proper prioritization"""
        # Add source type markers
        for article in rss_articles:
            article["source_type"] = "rss"

        for article in scraping_articles:
            article["source_type"] = "webscraping"
            # source_credibility already set in WebScrapingParser

        for article in newsapi_articles:
            article["source_type"] = "newsapi"
            article["source_credibility"] = 0.3  # Lower credibility for general news

        # Combine all articles
        all_articles = rss_articles + scraping_articles + newsapi_articles

        # Calculate relevancy scores
        scored_articles = self.calculate_relevancy_scores(all_articles)

        # Deduplicate
        deduplicated = self.deduplicate_articles(scored_articles)

        # Sort by relevancy score and recency
        deduplicated.sort(key=lambda x: (x["relevance_score"], x["published_at"]), reverse=True)

        return deduplicated

    def calculate_relevancy_scores(self, articles):
        """Calculate climbing-specific relevancy scores"""
        for article in articles:
            score = 0.0

            title_lower = article.get("title", "").lower()
            summary_lower = article.get("summary", "").lower()
            content = f"{title_lower} {summary_lower}"

            # Base score from source credibility
            score += article.get("source_credibility", 0.5) * 2

            # RSS sources get automatic boost
            if article.get("source_type") == "rss":
                score += 3.0

            # Web scraping sources get higher boost (specialized climbing sites)
            elif article.get("source_type") == "webscraping":
                score += 3.5

            # Climbing-specific keywords (higher scores for specialized terms)
            climbing_keywords = {
                # High-value terms
                "alpine climbing": 3.0,
                "alpinism": 3.0,
                "mountaineering": 2.5,
                "sport climbing": 2.5,
                "trad climbing": 2.5,
                "bouldering": 2.0,
                "free climbing": 2.0,
                "aid climbing": 2.0,
                # Competition and achievements
                "ifsc": 2.5,
                "world cup": 2.0,
                "competition": 1.5,
                "first ascent": 3.0,
                "new route": 2.5,
                "expedition": 2.0,
                # Gear and technical
                "climbing gear": 1.5,
                "equipment": 1.0,
                "safety": 1.5,
                "rope": 1.0,
                "harness": 1.0,
                "helmet": 1.0,
                # General climbing terms
                "climbing": 1.0,
                "climber": 1.0,
                "rock climbing": 1.5,
                "ice climbing": 2.0,
                "mixed climbing": 2.0,
            }

            for keyword, weight in climbing_keywords.items():
                if keyword in content:
                    score += weight

            # Slovenian content boost
            slovenian_terms = [
                "slovenia",
                "slovenian",
                "janja garnbret",
                "luka lindič",
                "ljubljana",
                "bled",
                "triglav",
                "julian alps",
            ]

            for term in slovenian_terms:
                if term in content:
                    score += 2.0  # Strong boost for Slovenian content
                    break

            # Famous climbers boost
            famous_climbers = [
                "adam ondra",
                "alex honnold",
                "lynn hill",
                "tommy caldwell",
                "janja garnbret",
                "shauna coxsey",
                "ashima shiraishi",
            ]

            for climber in famous_climbers:
                if climber in content:
                    score += 1.5
                    break

            # Recency bonus
            try:
                pub_date_str = article.get("published_at", "")
                if pub_date_str:
                    if "T" in pub_date_str:
                        pub_date = datetime.datetime.fromisoformat(
                            pub_date_str.replace("Z", "+00:00")
                        )
                    else:
                        pub_date = datetime.datetime.fromisoformat(pub_date_str)

                    time_diff = datetime.datetime.utcnow() - pub_date.replace(tzinfo=None)
                    if time_diff.total_seconds() < 24 * 3600:  # Within 24 hours
                        score += 2.0
                    elif time_diff.total_seconds() < 48 * 3600:  # Within 48 hours
                        score += 1.0
            except Exception:
                pass

            article["relevance_score"] = score

        return articles

    def deduplicate_articles(self, articles):
        """Remove duplicate articles, preferring higher-scored sources"""
        seen_titles = {}
        deduplicated = []

        # Sort by relevance score first for deduplication priority
        articles_sorted = sorted(articles, key=lambda x: x.get("relevance_score", 0), reverse=True)

        for article in articles_sorted:
            title = article.get("title", "").lower().strip()

            # Skip if we've seen a similar title
            is_duplicate = False
            for seen_title in seen_titles:
                if self._titles_similar(title, seen_title):
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen_titles[title] = article
                deduplicated.append(article)

        return deduplicated

    def _titles_similar(self, title1, title2, threshold=0.8):
        """Check if two titles are similar (simple word-based comparison)"""
        if not title1 or not title2:
            return False

        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())

        if not words1 or not words2:
            return False

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        similarity = len(intersection) / len(union)
        return similarity >= threshold

    def _fetch_newsapi_fallback(self):
        """Fetch from NewsAPI as fallback (existing logic)"""
        try:
            api_key = current_app.config.get("NEWS_API_KEY")
            if not api_key:
                return []

            newsapi = NewsApiClient(api_key=api_key)

            # Simplified NewsAPI search for fallback
            search_terms = ["rock climbing", "mountaineering", "alpine climbing"]
            all_articles = []

            end_time = datetime.datetime.utcnow()
            start_time = end_time - datetime.timedelta(days=7)
            from_date = start_time.strftime("%Y-%m-%d")

            for term in search_terms:
                try:
                    response = newsapi.get_everything(
                        q=term,
                        from_param=from_date,
                        language="en",
                        sort_by="relevancy",
                        page_size=3,  # Limited fallback
                    )

                    articles = response.get("articles", [])
                    for article in articles:
                        formatted = {
                            "title": article.get("title", ""),
                            "url": article.get("url", ""),
                            "summary": article.get("description", ""),
                            "published_at": article.get("publishedAt", ""),
                            "source": "newsapi",
                            "language": "en",
                        }
                        all_articles.append(formatted)

                except Exception as e:
                    current_app.logger.warning(f"NewsAPI fallback error for '{term}': {e}")
                    continue

            return all_articles

        except Exception as e:
            current_app.logger.error(f"NewsAPI fallback failed: {e}")
            return []

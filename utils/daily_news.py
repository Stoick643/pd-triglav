import datetime
import os
import re
from newsapi import NewsApiClient
from flask import current_app
import feedparser
from urllib.parse import urlparse
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
            is_slovenian = any(term in content_lower for term in [
                'slovenia', 'slovenian', 'janja garnbret', 'luka lindič'
            ])
            
            if is_slovenian and slovenian_count < max_slovenian:
                final_articles.append(article)
                slovenian_count += 1
            elif not is_slovenian:
                final_articles.append(article)
        
        # Format for database caching (maintain existing format)
        summaries = []
        for article in final_articles:
            summaries.append({
                "title": article.get('title', ''),
                "url": article.get('url', ''),
                "summary": article.get('summary', 'No description available'),
                "published_at": article.get('published_at', ''),
                "language": article.get('language', 'en'),
                "source": article.get('source', 'unknown'),
                "source_name": article.get('source_name', '')
            })
        
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
        api_key = current_app.config.get('NEWS_API_KEY')
        if not api_key:
            current_app.logger.warning("No NEWS_API_KEY configured")
            return []
        
        newsapi = NewsApiClient(api_key=api_key)
        
        # Simplified search for fallback
        search_terms = ["rock climbing", "mountaineering", "alpine climbing"]
        all_articles = []
        
        end_time = datetime.datetime.utcnow()
        start_time = end_time - datetime.timedelta(days=7)
        from_date = start_time.strftime('%Y-%m-%d')
        
        for term in search_terms:
            try:
                response = newsapi.get_everything(
                    q=term,
                    from_param=from_date,
                    language='en',
                    sort_by='relevancy',
                    page_size=3
                )
                
                articles = response.get('articles', [])
                for article in articles:
                    formatted = {
                        'title': article.get('title', ''),
                        'url': article.get('url', ''),
                        'summary': article.get('description', ''),
                        'published_at': article.get('publishedAt', ''),
                        'source': 'newsapi',
                        'language': 'en'
                    }
                    all_articles.append(formatted)
                    
            except Exception as e:
                current_app.logger.warning(f"NewsAPI fallback error for '{term}': {e}")
                continue
        
        # Simple deduplication and selection
        unique_articles = {}
        for article in all_articles:
            if article['url']:
                unique_articles[article['url']] = article
        
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
        'planetmountain': {
            'url': 'https://www.planetmountain.com/en/rss.xml',
            'name': 'PlanetMountain',
            'credibility': 1.0,
            'language': 'en'
        },
        'gripped': {
            'url': 'https://gripped.com/feed/',
            'name': 'Gripped Magazine',
            'credibility': 0.9,
            'language': 'en'
        },
        'ukclimbing': {
            'url': 'https://www.ukclimbing.com/news/rss',
            'name': 'UK Climbing',
            'credibility': 0.85,
            'language': 'en'
        },
        '8a': {
            'url': 'https://www.8a.nu/rss/',
            'name': '8a.nu',
            'credibility': 0.8,
            'language': 'en'
        }
    }
    
    def __init__(self):
        self.timeout = 10  # seconds
    
    def parse_feed(self, url, source_name=None):
        """Parse a single RSS feed and return formatted articles"""
        try:
            # Parse RSS feed with timeout
            feed = feedparser.parse(url)
            
            # Check for parse errors
            if hasattr(feed, 'bozo') and feed.bozo:
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
                    raw_summary = entry.get('summary', entry.get('description', ''))
                    
                    article = {
                        'title': entry.get('title', '').strip(),
                        'url': entry.get('link', ''),
                        'summary': self._clean_html_content(raw_summary),
                        'published_at': self._parse_date(entry),
                        'source': source_name,
                        'language': 'en'  # Default to English for now
                    }
                    
                    # Skip articles without essential data or meaningful content
                    if (article['title'] and article['url'] and 
                        article['summary'] and len(article['summary']) > 20):
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
                articles = self.parse_feed(source_config['url'], source_key)
                
                # Add source metadata to articles
                for article in articles:
                    article['source_credibility'] = source_config['credibility']
                    article['source_name'] = source_config['name']
                
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
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Extract main domain name
            source_name = domain.split('.')[0]
            
            # Handle special cases
            if '8a' in domain:
                return '8a'
            
            return source_name
            
        except:
            return 'unknown'
    
    def _parse_date(self, entry):
        """Parse RSS entry date to ISO format"""
        try:
            # Try different date fields that RSS feeds might use
            date_fields = ['published_parsed', 'updated_parsed']
            
            for field in date_fields:
                if hasattr(entry, field):
                    parsed_time = getattr(entry, field)
                    if parsed_time:
                        dt = datetime.datetime(*parsed_time[:6])
                        return dt.isoformat() + 'Z'
            
            # Fallback to string parsing
            date_str = entry.get('published', entry.get('updated', ''))
            if date_str:
                # Try to parse common RSS date formats
                try:
                    dt = datetime.datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
                    return dt.isoformat()
                except:
                    # If parsing fails, return current time
                    pass
            
            # Default to current time if no date found
            return datetime.datetime.utcnow().isoformat() + 'Z'
            
        except Exception as e:
            current_app.logger.warning(f"Date parsing error: {e}")
            return datetime.datetime.utcnow().isoformat() + 'Z'
    
    def _clean_html_content(self, html_text):
        """Clean HTML content and remove unwanted patterns"""
        if not html_text:
            return ''
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_text, 'html.parser')
            
            # Get plain text without HTML tags
            text = soup.get_text()
            
            # Remove common RSS footer patterns
            footer_patterns = [
                r'The post .+ appeared first on .+',
                r'Continue reading .+',
                r'Read more about .+',
                r'View this post on .+',
                r'Originally published on .+',
                r'Source: .+',
                r'\[.+\]$',  # Remove content in square brackets at end
            ]
            
            for pattern in footer_patterns:
                text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
            
            # Clean up whitespace and normalize text
            text = re.sub(r'\s+', ' ', text)  # Replace multiple whitespace with single space
            text = text.strip()
            
            # Remove trailing periods and common sentence enders if they seem incomplete
            if text.endswith('...') or text.endswith('….'):
                text = text.rstrip('.… ')
            
            # Ensure reasonable length (truncate at sentence boundary if too long)
            if len(text) > 300:
                # Try to cut at sentence boundary
                sentences = text.split('. ')
                truncated = ''
                for sentence in sentences:
                    if len(truncated + sentence + '. ') <= 300:
                        truncated += sentence + '. '
                    else:
                        break
                
                if truncated:
                    text = truncated.strip()
                else:
                    # Fallback: cut at word boundary
                    words = text.split()[:50]  # Approximately 300 chars
                    text = ' '.join(words)
                    if not text.endswith('.'):
                        text += '...'
            
            return text
            
        except Exception as e:
            current_app.logger.warning(f"HTML cleaning error: {e}")
            # Fallback: basic HTML tag removal with regex
            text = re.sub(r'<[^>]+>', '', html_text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:300] + ('...' if len(text) > 300 else '')


class ClimbingNewsAggregator:
    """Aggregate and score news from multiple sources"""
    
    def __init__(self):
        self.rss_parser = RSSFeedParser()
    
    def fetch_all_news(self):
        """Fetch news from all sources (RSS + NewsAPI fallback)"""
        # Start with RSS feeds
        rss_articles = self.rss_parser.fetch_all_feeds()
        
        # Get NewsAPI articles as fallback
        newsapi_articles = self._fetch_newsapi_fallback()
        
        # Combine sources with RSS priority
        return self.combine_sources(rss_articles, newsapi_articles)
    
    def combine_sources(self, rss_articles, newsapi_articles):
        """Combine RSS and NewsAPI articles with proper prioritization"""
        # Add source type markers
        for article in rss_articles:
            article['source_type'] = 'rss'
        
        for article in newsapi_articles:
            article['source_type'] = 'newsapi'
            article['source_credibility'] = 0.3  # Lower credibility for general news
        
        # Combine all articles
        all_articles = rss_articles + newsapi_articles
        
        # Calculate relevancy scores
        scored_articles = self.calculate_relevancy_scores(all_articles)
        
        # Deduplicate
        deduplicated = self.deduplicate_articles(scored_articles)
        
        # Sort by relevancy score and recency
        deduplicated.sort(key=lambda x: (x['relevance_score'], x['published_at']), reverse=True)
        
        return deduplicated
    
    def calculate_relevancy_scores(self, articles):
        """Calculate climbing-specific relevancy scores"""
        for article in articles:
            score = 0.0
            
            title_lower = article.get('title', '').lower()
            summary_lower = article.get('summary', '').lower()
            content = f"{title_lower} {summary_lower}"
            
            # Base score from source credibility
            score += article.get('source_credibility', 0.5) * 2
            
            # RSS sources get automatic boost
            if article.get('source_type') == 'rss':
                score += 3.0
            
            # Climbing-specific keywords (higher scores for specialized terms)
            climbing_keywords = {
                # High-value terms
                'alpine climbing': 3.0, 'alpinism': 3.0, 'mountaineering': 2.5,
                'sport climbing': 2.5, 'trad climbing': 2.5, 'bouldering': 2.0,
                'free climbing': 2.0, 'aid climbing': 2.0,
                
                # Competition and achievements
                'ifsc': 2.5, 'world cup': 2.0, 'competition': 1.5,
                'first ascent': 3.0, 'new route': 2.5, 'expedition': 2.0,
                
                # Gear and technical
                'climbing gear': 1.5, 'equipment': 1.0, 'safety': 1.5,
                'rope': 1.0, 'harness': 1.0, 'helmet': 1.0,
                
                # General climbing terms
                'climbing': 1.0, 'climber': 1.0, 'rock climbing': 1.5,
                'ice climbing': 2.0, 'mixed climbing': 2.0
            }
            
            for keyword, weight in climbing_keywords.items():
                if keyword in content:
                    score += weight
            
            # Slovenian content boost
            slovenian_terms = [
                'slovenia', 'slovenian', 'janja garnbret', 'luka lindič',
                'ljubljana', 'bled', 'triglav', 'julian alps'
            ]
            
            for term in slovenian_terms:
                if term in content:
                    score += 2.0  # Strong boost for Slovenian content
                    break
            
            # Famous climbers boost
            famous_climbers = [
                'adam ondra', 'alex honnold', 'lynn hill', 'tommy caldwell',
                'janja garnbret', 'shauna coxsey', 'ashima shiraishi'
            ]
            
            for climber in famous_climbers:
                if climber in content:
                    score += 1.5
                    break
            
            # Recency bonus
            try:
                pub_date_str = article.get('published_at', '')
                if pub_date_str:
                    if 'T' in pub_date_str:
                        pub_date = datetime.datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                    else:
                        pub_date = datetime.datetime.fromisoformat(pub_date_str)
                    
                    time_diff = datetime.datetime.utcnow() - pub_date.replace(tzinfo=None)
                    if time_diff.total_seconds() < 24 * 3600:  # Within 24 hours
                        score += 2.0
                    elif time_diff.total_seconds() < 48 * 3600:  # Within 48 hours
                        score += 1.0
            except:
                pass
            
            article['relevance_score'] = score
        
        return articles
    
    def deduplicate_articles(self, articles):
        """Remove duplicate articles, preferring higher-scored sources"""
        seen_titles = {}
        deduplicated = []
        
        # Sort by relevance score first for deduplication priority
        articles_sorted = sorted(articles, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        for article in articles_sorted:
            title = article.get('title', '').lower().strip()
            
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
            api_key = current_app.config.get('NEWS_API_KEY')
            if not api_key:
                return []
            
            newsapi = NewsApiClient(api_key=api_key)
            
            # Simplified NewsAPI search for fallback
            search_terms = ['rock climbing', 'mountaineering', 'alpine climbing']
            all_articles = []
            
            end_time = datetime.datetime.utcnow()
            start_time = end_time - datetime.timedelta(days=7)
            from_date = start_time.strftime('%Y-%m-%d')
            
            for term in search_terms:
                try:
                    response = newsapi.get_everything(
                        q=term,
                        from_param=from_date,
                        language='en',
                        sort_by='relevancy',
                        page_size=3  # Limited fallback
                    )
                    
                    articles = response.get('articles', [])
                    for article in articles:
                        formatted = {
                            'title': article.get('title', ''),
                            'url': article.get('url', ''),
                            'summary': article.get('description', ''),
                            'published_at': article.get('publishedAt', ''),
                            'source': 'newsapi',
                            'language': 'en'
                        }
                        all_articles.append(formatted)
                        
                except Exception as e:
                    current_app.logger.warning(f"NewsAPI fallback error for '{term}': {e}")
                    continue
            
            return all_articles
            
        except Exception as e:
            current_app.logger.error(f"NewsAPI fallback failed: {e}")
            return []
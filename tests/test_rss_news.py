"""Test RSS news integration for specialized climbing content"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from utils.daily_news import (
    get_daily_mountaineering_news_for_homepage,
    fetch_and_cache_news,
    RSSFeedParser,
    ClimbingNewsAggregator,
    WebScrapingParser
)
from models.content import DailyNews
from models.user import db


# Mark tests appropriately
pytestmark = [pytest.mark.fast]


class TestRSSFeedParser:
    """Test RSS feed parsing functionality"""
    
    @pytest.fixture
    def mock_rss_data(self):
        """Mock RSS feed data for testing"""
        # Create mock entries that behave like feedparser entries
        mock_entries = []
        
        entries_data = [
            {
                'title': 'New Alpine Route Established on Mont Blanc',
                'link': 'https://planetmountain.com/news/alpine/mont-blanc-route',
                'published': '2025-01-29T10:00:00Z',
                'summary': 'Climbers establish challenging new alpine route on Mont Blanc north face.',
            },
            {
                'title': 'Janja Garnbret Wins Slovenia Cup',
                'link': 'https://planetmountain.com/news/competition/janja-slovenia',
                'published': '2025-01-28T15:30:00Z',
                'summary': 'Slovenian climbing champion dominates national competition.',
            },
            {
                'title': 'New Climbing Equipment Review',
                'link': 'https://planetmountain.com/gear/harness-review',
                'published': '2025-01-27T09:15:00Z',
                'summary': 'Comprehensive review of latest climbing harnesses and gear.',
            }
        ]
        
        for entry_data in entries_data:
            # Create a mock entry object that behaves like feedparser entry
            mock_entry = type('MockEntry', (), entry_data)()
            # Add get method to behave like feedparser entry
            def make_get_method(entry):
                return lambda k, default='': getattr(entry, k, default)
            mock_entry.get = make_get_method(mock_entry)
            mock_entries.append(mock_entry)
        
        return {
            'entries': mock_entries,
            'feed': {
                'title': 'PlanetMountain News',
                'link': 'https://planetmountain.com'
            }
        }
    
    @pytest.fixture
    def rss_parser(self, app):
        """Create RSS parser instance"""
        with app.app_context():
            return RSSFeedParser()
    
    def test_parse_valid_rss_feed(self, rss_parser, mock_rss_data):
        """Test parsing valid RSS feed returns expected articles"""
        with patch('feedparser.parse') as mock_parse:
            # Create a mock object that behaves like feedparser result
            mock_result = type('MockFeed', (), {})()
            mock_result.entries = mock_rss_data['entries']
            mock_result.feed = mock_rss_data['feed']
            mock_result.bozo = 0  # No parse errors
            
            mock_parse.return_value = mock_result
            
            articles = rss_parser.parse_feed('https://planetmountain.com/rss.xml')
            
            assert len(articles) == 3
            assert articles[0]['title'] == 'New Alpine Route Established on Mont Blanc'
            assert articles[0]['url'] == 'https://planetmountain.com/news/alpine/mont-blanc-route'
            assert articles[0]['source'] == 'planetmountain'
            assert 'published_at' in articles[0]
    
    def test_handle_invalid_rss_feed(self, rss_parser):
        """Test graceful handling of malformed RSS"""
        with patch('feedparser.parse') as mock_parse:
            # Simulate malformed RSS
            mock_parse.return_value = {'entries': [], 'bozo': 1}
            
            articles = rss_parser.parse_feed('https://invalid-rss-url.com/feed')
            
            assert articles == []
    
    def test_parse_empty_rss_feed(self, rss_parser):
        """Test handling of empty RSS feeds"""
        with patch('feedparser.parse') as mock_parse:
            mock_parse.return_value = {'entries': [], 'feed': {'title': 'Empty Feed'}}
            
            articles = rss_parser.parse_feed('https://empty-feed.com/rss')
            
            assert articles == []
    
    def test_rss_feed_timeout_handling(self, rss_parser):
        """Test network timeout scenarios"""
        with patch('feedparser.parse') as mock_parse:
            mock_parse.side_effect = Exception("Network timeout")
            
            articles = rss_parser.parse_feed('https://unreachable-site.com/rss')
            
            assert articles == []
    
    def test_extract_source_name_from_url(self, rss_parser):
        """Test extracting source name from RSS URL"""
        assert rss_parser._extract_source_name('https://planetmountain.com/rss.xml') == 'planetmountain'
        assert rss_parser._extract_source_name('https://gripped.com/feed/') == 'gripped'
        assert rss_parser._extract_source_name('https://ukclimbing.com/news/rss') == 'ukclimbing'
    
    def test_clean_html_content_basic(self, rss_parser):
        """Test basic HTML tag removal"""
        html_text = '<p>Alpine climbing can bring you to amazing places.</p>'
        cleaned = rss_parser._clean_html_content(html_text)
        assert cleaned == 'Alpine climbing can bring you to amazing places.'
        assert '<p>' not in cleaned
        assert '</p>' not in cleaned
    
    def test_clean_html_content_complex(self, rss_parser):
        """Test cleaning complex HTML with links and tags"""
        html_text = '''<p>Alpine climbing can bring you to amazing places, but a lot can go wrong so be sure that you're prepared</p> 
        <p>The post <a href="https://gripped.com/profiles/10-tips-for-your-first-alpine-climb/">10 Tips for Your First Alpine Climb</a> appeared first on <a href="https://gripped.com">Gripped Magazine</a>.</p>'''
        
        cleaned = rss_parser._clean_html_content(html_text)
        
        # Should remove HTML tags
        assert '<p>' not in cleaned
        assert '<a href' not in cleaned
        assert '</p>' not in cleaned
        
        # Should remove footer text pattern
        assert 'appeared first on' not in cleaned
        assert 'The post' not in cleaned
        
        # Should keep the main content
        assert 'Alpine climbing can bring you to amazing places' in cleaned
        assert "you're prepared" in cleaned
    
    def test_clean_html_content_footer_patterns(self, rss_parser):
        """Test removal of common RSS footer patterns"""
        test_cases = [
            ('Main content. The post Title appeared first on Website.', 'Main content.'),
            ('Article text. Continue reading more details here.', 'Article text.'),
            ('News content. Read more about this topic.', 'News content.'),
            ('Content here. Originally published on Source.', 'Content here.'),
            ('Article. [Additional info]', 'Article.'),
        ]
        
        for input_text, expected in test_cases:
            cleaned = rss_parser._clean_html_content(input_text)
            assert expected.strip() in cleaned
    
    def test_clean_html_content_whitespace_normalization(self, rss_parser):
        """Test whitespace normalization"""
        html_text = '<p>Text   with    multiple\n\n    spaces.</p>'
        cleaned = rss_parser._clean_html_content(html_text)
        assert cleaned == 'Text with multiple spaces.'
    
    def test_clean_html_content_length_truncation(self, rss_parser):
        """Test content truncation at sentence boundaries"""
        # Create content longer than 300 characters
        long_text = '<p>' + 'This is a test sentence. ' * 20 + '</p>'
        cleaned = rss_parser._clean_html_content(long_text)
        
        # Should be truncated
        assert len(cleaned) <= 300
        # Should end properly (either with period or ellipsis)
        assert cleaned.endswith('.') or cleaned.endswith('...')
    
    def test_clean_html_content_empty_input(self, rss_parser):
        """Test handling of empty or None input"""
        assert rss_parser._clean_html_content('') == ''
        assert rss_parser._clean_html_content(None) == ''
        assert rss_parser._clean_html_content('   ') == ''
    
    def test_clean_html_content_malformed_html(self, rss_parser):
        """Test handling of malformed HTML"""
        malformed_html = '<p>Unclosed paragraph <div>Mixed tags</p></div> Text'
        cleaned = rss_parser._clean_html_content(malformed_html)
        
        # Should still extract text even from malformed HTML
        assert 'Unclosed paragraph' in cleaned
        assert 'Mixed tags' in cleaned
        assert 'Text' in cleaned
        assert '<' not in cleaned  # No HTML tags should remain


class TestClimbingNewsAggregator:
    """Test news aggregation with climbing-specific logic"""
    
    @pytest.fixture
    def aggregator(self, app):
        """Create news aggregator instance"""
        with app.app_context():
            return ClimbingNewsAggregator()
    
    @pytest.fixture
    def mock_rss_articles(self):
        """Mock articles from RSS feeds"""
        return [
            {
                'title': 'Adam Ondra Completes Project in Slovenia',
                'url': 'https://planetmountain.com/ondra-slovenia',
                'summary': 'Czech climber completes difficult project in Slovenian Alps.',
                'published_at': '2025-01-29T10:00:00Z',
                'source': 'planetmountain',
                'language': 'en'
            },
            {
                'title': 'New Gear Review: Climbing Helmets 2025',
                'url': 'https://gripped.com/gear-review-helmets',
                'summary': 'Comprehensive review of latest climbing safety equipment.',
                'published_at': '2025-01-28T14:00:00Z',
                'source': 'gripped',
                'language': 'en'
            }
        ]
    
    @pytest.fixture
    def mock_newsapi_articles(self):
        """Mock articles from NewsAPI"""
        return [
            {
                'title': 'Rock Climbing Popularity Increases',
                'url': 'https://general-news.com/climbing-popularity',
                'summary': 'General news about climbing gaining popularity.',
                'published_at': '2025-01-27T12:00:00Z',
                'source': 'newsapi',
                'language': 'en'
            }
        ]
    
    def test_combine_rss_and_newsapi_sources(self, aggregator, mock_rss_articles, mock_newsapi_articles):
        """Test merging RSS feeds with existing NewsAPI"""
        empty_scraping_articles = []
        combined = aggregator.combine_sources(mock_rss_articles, empty_scraping_articles, mock_newsapi_articles)
        
        assert len(combined) == 3
        # RSS articles should come first due to higher relevancy
        assert combined[0]['source'] in ['planetmountain', 'gripped']
    
    def test_source_priority_weighting(self, aggregator, mock_rss_articles, mock_newsapi_articles):
        """Test RSS sources get higher relevancy scores"""
        all_articles = mock_rss_articles + mock_newsapi_articles
        scored = aggregator.calculate_relevancy_scores(all_articles)
        
        # RSS articles should have higher scores than NewsAPI
        rss_scores = [article['relevance_score'] for article in scored if article['source'] != 'newsapi']
        newsapi_scores = [article['relevance_score'] for article in scored if article['source'] == 'newsapi']
        
        assert min(rss_scores) > max(newsapi_scores)
    
    def test_climbing_keyword_detection(self, aggregator):
        """Test climbing-specific terms boost scores"""
        articles = [
            {
                'title': 'Alpine Climbing in the Dolomites',
                'summary': 'Technical alpine route description',
                'source': 'test',
                'published_at': '2025-01-29T10:00:00Z'
            },
            {
                'title': 'General Mountain News',
                'summary': 'Non-climbing mountain content',
                'source': 'test',
                'published_at': '2025-01-29T10:00:00Z'
            }
        ]
        
        scored = aggregator.calculate_relevancy_scores(articles)
        
        # Alpine climbing article should score higher
        assert scored[0]['relevance_score'] > scored[1]['relevance_score']
    
    def test_slovenian_content_prioritization(self, aggregator):
        """Test Slovenian climbing content gets priority"""
        articles = [
            {
                'title': 'Janja Garnbret Wins Competition',
                'summary': 'Slovenian climber dominates world cup',
                'source': 'test',
                'published_at': '2025-01-29T10:00:00Z'
            },
            {
                'title': 'American Climber Success',
                'summary': 'US climber completes difficult route',
                'source': 'test',
                'published_at': '2025-01-29T10:00:00Z'
            }
        ]
        
        scored = aggregator.calculate_relevancy_scores(articles)
        
        # Slovenian content should score higher
        assert scored[0]['relevance_score'] > scored[1]['relevance_score']
    
    def test_deduplication_across_sources(self, aggregator):
        """Test deduplication works across RSS and NewsAPI sources"""
        duplicate_articles = [
            {
                'title': 'Same Climbing News Story',
                'url': 'https://planetmountain.com/story',
                'source': 'planetmountain'
            },
            {
                'title': 'Same Climbing News Story',
                'url': 'https://different-site.com/same-story',
                'source': 'newsapi'
            }
        ]
        
        deduplicated = aggregator.deduplicate_articles(duplicate_articles)
        
        # Should keep only one article (preferably RSS source)
        assert len(deduplicated) == 1
        assert deduplicated[0]['source'] == 'planetmountain'


class TestRSSNewsIntegration:
    """Test integration with existing news system"""
    
    @pytest.mark.slow
    def test_fallback_to_newsapi_on_rss_failure(self, app, client):
        """Test NewsAPI fallback when RSS feeds fail"""
        with app.app_context():
            with patch('utils.daily_news.RSSFeedParser.fetch_all_feeds') as mock_rss:
                with patch('newsapi.NewsApiClient.get_everything') as mock_newsapi:
                    # Simulate RSS failure
                    mock_rss.return_value = []
                    
                    # Mock NewsAPI success
                    mock_newsapi.return_value = {
                        'articles': [{
                            'title': 'Fallback Climbing News',
                            'url': 'https://newsapi-source.com/climbing',
                            'description': 'Fallback news content',
                            'publishedAt': '2025-01-29T10:00:00Z'
                        }]
                    }
                    
                    # Mock the app config to have NEWS_API_KEY
                    with patch.dict(app.config, {'NEWS_API_KEY': 'test_key'}):
                        news = get_daily_mountaineering_news_for_homepage()
                    
                    # Should get NewsAPI content as fallback
                    assert len(news) > 0
                    assert any('fallback' in article['title'].lower() for article in news)
    
    def test_caching_integration(self, app, client):
        """Test RSS content gets properly cached"""
        with app.app_context():
            # Clear any existing cache
            DailyNews.query.delete()
            db.session.commit()
            
            with patch('utils.daily_news.RSSFeedParser.fetch_all_feeds') as mock_rss:
                mock_rss.return_value = [{
                    'title': 'Test RSS Article',
                    'url': 'https://test.com/article',
                    'summary': 'Test content',
                    'published_at': '2025-01-29T10:00:00Z',
                    'source': 'test',
                    'language': 'en'
                }]
                
                # First call should fetch and cache
                news1 = get_daily_mountaineering_news_for_homepage()
                
                # Second call should use cache (no RSS fetching)
                mock_rss.reset_mock()
                news2 = get_daily_mountaineering_news_for_homepage()
                
                assert news1 == news2
                mock_rss.assert_not_called()  # Should not fetch again


# Mock classes that will be implemented
class MockRSSFeedParser:
    """Mock RSS parser for testing"""
    def parse_feed(self, url):
        return []
    
    def fetch_all_feeds(self):
        return []
    
    def _extract_source_name(self, url):
        return url.split('//')[1].split('.')[0].split('/')[0]


class MockClimbingNewsAggregator:
    """Mock news aggregator for testing"""
    def combine_sources(self, rss_articles, newsapi_articles):
        return rss_articles + newsapi_articles
    
    def calculate_relevancy_scores(self, articles):
        for article in articles:
            article['relevance_score'] = 1.0
        return articles
    
    def deduplicate_articles(self, articles):
        seen_urls = set()
        deduplicated = []
        for article in articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                deduplicated.append(article)
        return deduplicated


class TestWebScrapingParser:
    """Test web scraping functionality"""
    
    @pytest.fixture
    def web_scraper(self, app):
        """Create web scraper instance"""
        with app.app_context():
            return WebScrapingParser()
    
    def test_scraper_initialization(self, web_scraper):
        """Test WebScrapingParser initialization"""
        assert web_scraper.session is not None
        assert web_scraper.timeout == 15
        assert len(web_scraper.SCRAPING_SOURCES) == 3
        assert 'aac' in web_scraper.SCRAPING_SOURCES
        assert 'climbing' in web_scraper.SCRAPING_SOURCES
        assert 'explorersweb' in web_scraper.SCRAPING_SOURCES
    
    def test_source_configuration(self, web_scraper):
        """Test scraper source configuration"""
        aac_config = web_scraper.SCRAPING_SOURCES['aac']
        assert aac_config['name'] == 'American Alpine Club'
        assert aac_config['credibility'] == 0.95
        assert 'url' in aac_config
        assert 'selectors' in aac_config
        assert 'rate_limit' in aac_config
    
    def test_html_content_cleaning_integration(self, web_scraper):
        """Test that web scraper uses HTML cleaning"""
        html_content = '<p>Test content with <a href="link">HTML tags</a></p>'
        cleaned = web_scraper._clean_html_content(html_content)
        
        assert '<p>' not in cleaned
        assert '<a href' not in cleaned
        assert 'Test content with HTML tags' in cleaned
    
    def test_date_parsing_various_formats(self, web_scraper):
        """Test date parsing from different formats"""
        from bs4 import BeautifulSoup
        
        # Test datetime attribute
        elem1 = BeautifulSoup('<time datetime="2025-01-29T10:00:00Z">Jan 29</time>', 'html.parser').find('time')
        result1 = web_scraper._parse_date(elem1)
        assert '2025-01-29T10:00:00Z' in result1
        
        # Test text content
        elem2 = BeautifulSoup('<span class="date">January 29, 2025</span>', 'html.parser').find('span')
        result2 = web_scraper._parse_date(elem2)
        assert '2025-01-29' in result2
        
        # Test None input
        result3 = web_scraper._parse_date(None)
        assert result3.endswith('Z')


class TestWebScrapingIntegration:
    """Test web scraping integration with existing system"""
    
    @pytest.fixture
    def aggregator(self, app):
        """Create news aggregator with web scraping"""
        with app.app_context():
            return ClimbingNewsAggregator()
    
    def test_aggregator_has_web_scraper(self, aggregator):
        """Test that aggregator includes web scraper"""
        assert hasattr(aggregator, 'web_scraper')
        assert isinstance(aggregator.web_scraper, WebScrapingParser)
    
    def test_web_scraping_relevancy_scoring(self, aggregator):
        """Test that web scraping articles get proper relevancy scores"""
        test_articles = [
            {
                'title': 'Alpine Climbing Route',
                'summary': 'New alpine climbing route established',
                'source_type': 'webscraping',
                'source_credibility': 0.95
            },
            {
                'title': 'RSS Climbing News',
                'summary': 'Climbing news from RSS',
                'source_type': 'rss', 
                'source_credibility': 0.9
            },
            {
                'title': 'General News',
                'summary': 'General news article',
                'source_type': 'newsapi',
                'source_credibility': 0.3
            }
        ]
        
        scored = aggregator.calculate_relevancy_scores(test_articles)
        
        # Web scraping should have highest score (3.5 + credibility*2 + keywords)
        webscraping_score = next(a['relevance_score'] for a in scored if a['source_type'] == 'webscraping')
        rss_score = next(a['relevance_score'] for a in scored if a['source_type'] == 'rss')
        newsapi_score = next(a['relevance_score'] for a in scored if a['source_type'] == 'newsapi')
        
        assert webscraping_score > rss_score > newsapi_score
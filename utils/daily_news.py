import datetime
import os
from newsapi import NewsApiClient
from flask import current_app

def get_daily_mountaineering_news_for_homepage():
    # Initialize NewsAPI client
    api_key = current_app.config.get('NEWS_API_KEY')
    if not api_key:
        return []
    
    newsapi = NewsApiClient(api_key=api_key)
    
    # Define the time window for "recent" news (e.g., last 7 days)
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(days=7) # Expanded to 7 days
    print(f"Fetching news from {start_time} to {end_time}")
    # Format dates for API calls (NewsAPI expects YYYY-MM-DD format)
    from_date = start_time.strftime('%Y-%m-%d')

    # Define your core search queries. You'll pass these to your news/search API.
    # The 'publishedAfter' parameter should be handled by your API client.
    search_terms = [
        "rock climbing",
        "mountaineering",
        "alpine climbing", 
        "climbing competition",
        "Alex Honnold",
        "Adam Ondra",
        "Janja Garnbret",
        "climbing equipment",
        "IFSC climbing",
        "Olympic climbing",
        "climbing gear 2025"
    ]

    all_fetched_articles = []
    
    # Search in both English and Slovenian
    languages = ['en']
    
    for language in languages:
        for term in search_terms:
            try:
                print(f"Searching for '{term}' in {language}...")
                
                # Use NewsAPI to get everything matching the search term
                response = newsapi.get_everything(
                    q=term,
                    from_param=from_date,  # Now using 7-day window
                    language=language,
                    sort_by='relevancy',
                    page_size=5  # Limit results per search
                )
                
                # Extract articles from response
                articles = response.get('articles', [])
                print(f"  Found {len(articles)} articles")
                
                # Convert to our format
                for article in articles:
                    formatted_article = {
                        'title': article.get('title', ''),
                        'url': article.get('url', ''),
                        'published_at': article.get('publishedAt', ''),
                        'description': article.get('description', ''),
                        'language': language
                    }
                    all_fetched_articles.append(formatted_article)
                    
            except Exception as e:
                # Log error but continue with other searches
                print(f"Error fetching news for '{term}' in {language}: {e}")
                continue

    # 1. Deduplication (important!)
    unique_articles = {}
    for article in all_fetched_articles:
        unique_articles[article['url']] = article # Using URL as a unique key

    deduplicated_list = list(unique_articles.values())

    # 2. Relevancy Scoring and Filtering
    scored_articles = []
    for article in deduplicated_list:
        score = 0
        title_lower = article.get('title', '').lower()
        url_lower = article.get('url', '').lower()

        # Prioritize Slovenian content
        if "slovenia" in title_lower or "slovenia" in url_lower or \
           "janja garnbret" in title_lower or "luka lindič" in title_lower:
            score += 5

        # Recentness bonus (already filtered by date, but can add fine-grained bonus)
        try:
            pub_date_str = article.get('published_at', '')
            if pub_date_str:
                # Handle different datetime formats from NewsAPI
                if 'T' in pub_date_str:
                    pub_date = datetime.datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                else:
                    pub_date = datetime.datetime.fromisoformat(pub_date_str)
                
                time_diff = end_time - pub_date.replace(tzinfo=None)
                if time_diff.total_seconds() < 24 * 3600: # Within last 24 hours
                    score += 3
                elif time_diff.total_seconds() < 48 * 3600: # Within last 48 hours
                    score += 1
        except (ValueError, AttributeError):
            # Skip if date parsing fails
            pass

        # Keywords relevancy
        if "alpinism" in title_lower: score += 2
        if "sport climbing" in title_lower: score += 2
        if "gear" in title_lower or "equipment" in title_lower: score += 1

        article['relevance_score'] = score
        scored_articles.append(article)

    # Sort by relevance and then by recency
    scored_articles.sort(key=lambda x: (x['relevance_score'], x['published_at']), reverse=True)

    # 3. Select Top 3 with "max 2 Slovenian" rule
    final_top_3 = []
    slovenian_count = 0
    for article in scored_articles:
        if len(final_top_3) == 3:
            break

        is_slovenian = False
        title_lower = article.get('title', '').lower()
        if "slovenia" in title_lower or "janja garnbret" in title_lower or \
           "luka lindič" in title_lower:
            is_slovenian = True

        if is_slovenian and slovenian_count < 2:
            final_top_3.append(article)
            slovenian_count += 1
        elif not is_slovenian:
            final_top_3.append(article)

    # 4. Use descriptions from NewsAPI (no LLM needed for first iteration)
    summaries = []
    for article in final_top_3:
        summaries.append({
            "title": article.get('title'),
            "url": article.get('url'),
            "summary": article.get('description', 'No description available'),
            "published_at": article.get('published_at'),
            "language": article.get('language', 'en')
        })

    return summaries

# This function would be called daily by your client's backend system.
# The `scheduler` tool in this environment is effectively doing something similar
# by triggering a specific prompt at a set interval.
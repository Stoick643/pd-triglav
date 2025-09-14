import os
import json
import feedparser
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict

# --- Configuration ---

# Load environment variables from .env file
load_dotenv()

# A list of RSS feeds to scrape. Add your curated sources here.
RSS_FEEDS = {
    "PZS": "https://www.pzs.si/rss.php",
    "Planet Mountain": "https://www.planetmountain.com/rss/rss.xml",
    "Gripped Magazine": "https://gripped.com/feed/",
    # Add more high-quality feeds here
}

# The number of news items you want in your final digest
NUM_DIGEST_ARTICLES = 5

# The output file for your website to use
OUTPUT_FILE = "todays_news.json"

# --- LLM Service (Modular Design) ---

class LLMService:
    """
    A modular class to handle interactions with an LLM API.
    Can be easily replaced with a different provider (e.g., AnthropicClaudeService).
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key not found. Please set the GOOGLE_API_KEY environment variable.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def select_best_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Uses the LLM to select the most relevant articles from a list.
        """
        print(f"🧠 Asking LLM to select the best {NUM_DIGEST_ARTICLES} articles from {len(articles)} options...")
        
        # Create a simplified list of articles for the prompt
        prompt_articles = [{"id": i, "title": a['title'], "source": a['source']} for i, a in enumerate(articles)]

        prompt = f"""
        You are the news editor for a Slovenian mountaineering club.
        From the following list of articles in JSON format, select the {NUM_DIGEST_ARTICLES} most important and interesting articles for our audience.
        Prioritize news from Slovenia first (e.g., from 'PZS'), then major European and world news.
        
        Your response MUST be a JSON array containing only the IDs of your selected articles, in order of importance. For example: [3, 0, 8, 5, 2]

        Here is the list of articles:
        {json.dumps(prompt_articles, indent=2)}
        """

        try:
            response = self.model.generate_content(prompt)
            # The response text might have markdown backticks, so we clean it.
            selected_ids_str = response.text.strip().replace("```json", "").replace("```", "").strip()
            selected_ids = json.loads(selected_ids_str)
            
            # Return the full article objects based on the selected IDs
            return [articles[i] for i in selected_ids if i < len(articles)]
        except Exception as e:
            print(f"❗️ LLM selection failed: {e}. Returning the first {NUM_DIGEST_ARTICLES} articles as a fallback.")
            return articles[:NUM_DIGEST_ARTICLES]

    def summarize_and_translate(self, article: Dict) -> Dict:
        """
        Uses the LLM to summarize and translate a single article.
        """
        print(f"✍️ Asking LLM to summarize: \"{article['title']}\"")
        
        prompt = f"""
        You are a helpful assistant for a mountaineering website.
        Analyze the following article title and summary:
        Title: {article['title']}
        Summary: {article['summary']}

        Your task is to:
        1. Write a concise, engaging 2-sentence summary in English.
        2. Provide a professional Slovenian translation of that summary.

        Your response MUST be a JSON object with two keys: "summary_en" and "summary_sl".
        """
        
        try:
            response = self.model.generate_content(prompt)
            summary_data = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            article.update(summary_data) # Add summaries to the article dict
            return article
        except Exception as e:
            print(f"❗️ LLM summarization failed for '{article['title']}': {e}")
            # Fallback: Use the original summary if AI fails
            article['summary_en'] = article['summary']
            article['summary_sl'] = "(Prevajanje ni uspelo)" # Translation failed
            return article


# --- Core Functions ---

def fetch_articles_from_rss(feeds: Dict[str, str]) -> List[Dict]:
    """
    Fetches and parses articles from a list of RSS feeds.
    """
    all_articles = []
    print("📰 Fetching articles from RSS feeds...")
    for source, url in feeds.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                all_articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.summary,
                    "source": source,
                })
        except Exception as e:
            print(f"❗️ Could not fetch or parse feed from {source} ({url}): {e}")
    return all_articles

def save_digest_to_json(articles: List[Dict]):
    """
    Saves the final list of curated articles to a JSON file.
    """
    print(f"\n✅ Success! Saving {len(articles)} articles to {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump({"articles": articles}, f, ensure_ascii=False, indent=2)

# --- Main Execution ---

def main():
    """
    The main function to orchestrate the entire process.
    """
    print("--- Starting Daily Mountaineering News Digest Generation ---")
    
    # 1. Initialize the LLM Service
    api_key = os.getenv("GOOGLE_API_KEY")
    llm_service = LLMService(api_key=api_key)

    # 2. Gather: Fetch all articles from RSS feeds
    raw_articles = fetch_articles_from_rss(RSS_FEEDS)
    if not raw_articles:
        print("No articles found. Exiting.")
        return

    # 3. Select: Use the LLM to curate the best articles
    selected_articles = llm_service.select_best_articles(raw_articles)
    
    # 4. Process: Summarize and translate each selected article
    final_digest = []
    for article in selected_articles:
        processed_article = llm_service.summarize_and_translate(article)
        final_digest.append(processed_article)

    # 5. Save: Store the final result in a JSON file
    save_digest_to_json(final_digest)
    print("--- Digest Generation Complete ---")


if __name__ == "__main__":
    main()
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from newsapi import NewsApiClient


API_KEY = "d642b2e2ef1a4b259f0d60b999512ab7"

newsapi = NewsApiClient(api_key=API_KEY)

def verify_news(news_text):

    try:

        clean_query = re.sub(r"[^a-zA-Z0-9 ]", " ", news_text)
        query = " ".join(clean_query.split()[:10])
        print("ORIGINAL NEWS:", news_text)
        print("SEARCH QUERY:", query)

        result = newsapi.get_everything(
            q=query,
            language="en",
            sort_by="relevancy",
            page_size=20
        )

        print("NEWS API RESPONSE:", result)

        articles = result.get("articles", [])

        print("Articles Found:", len(articles))
        if len(articles) == 0:
            return {
                "verified": False,
                "source": "",
                "url": "",
                "title": "",
                "label": -1,
                "similarity": 0
            }

        trusted_sources = [
            "BBC",
            "BBC News",
            "Reuters",
            "Associated Press",
            "AP News",
            "CNN",
            "The Hindu",
            "Times of India",
            "The Times of India",
            "Indian Express",
            "The Indian Express",
            "NDTV",
            "India Today",
            "Hindustan Times",
            "Business Standard",
            "Economic Times",
            "Mint",
            "ANI",
            "ABC News",
            "The Guardian",
            "CNBC",
            "Bloomberg",
            "Al Jazeera"
        ]

        best_article = None
        best_similarity = 0
        best_trusted = False

        for article in articles:

            title = article.get("title", "")
            description = article.get("description", "")

            article_text = f"{title} {description}".strip()

            if article_text == "":
                continue

            tfidf = TfidfVectorizer(stop_words="english")

            vectors = tfidf.fit_transform([
                news_text.lower(),
                article_text.lower()
            ])

            similarity = cosine_similarity(
                vectors[0:1],
                vectors[1:2]
            )[0][0]

            source = (article.get("source") or {}).get("name", "")

            trusted = any(
                s.lower() in source.lower()
                for s in trusted_sources
            )

            print("--------------------------------")
            print("Source:", source)
            print("Title:", title)
            print("Similarity:", round(similarity * 100, 2))
            print("Trusted:", trusted)

            if similarity > best_similarity:
                best_similarity = similarity
                best_article = article
                best_trusted = trusted

        if best_article is None:
            return {
                "verified": False,
                "source": "",
                "url": "",
                "title": "",
                "label": -1,
                "similarity": 0
            }

        source = (best_article.get("source") or {}).get("name", "")
        title = best_article.get("title", "")
        url = best_article.get("url", "")

        similarity_percent = round(best_similarity * 100, 2)

        print("\n===== BEST MATCH =====")
        print("Source:", source)
        print("Title:", title)
        print("Similarity:", similarity_percent)
        print("Trusted:", best_trusted)
        print("URL:", url)

        if best_trusted and best_similarity >= 0.10:
            verified = True
            label = 1

        elif best_similarity >= 0.50:
            verified = True
            label = 1

        else:
            verified = False
            label = -1

        return {
            "verified": verified,
            "source": source,
            "url": url,
            "title": title,
            "label": label,
            "similarity": similarity_percent
        }

    except Exception as e:

        print("NewsAPI Error:", e)

        return {
            "verified": False,
            "source": "",
            "url": "",
            "title": "",
            "label": -1,
            "similarity": 0
        }

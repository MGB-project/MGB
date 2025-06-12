import requests
import time

API_URL = "https://api.igdb.com/v4/games"
HEADERS = {
    "Client-ID": "o1fqvvct2tz1j121vbcqdqbpejpkgv",
    "Authorization": "Bearer 7p6w6d9j8yzy87bc81mkoaqbjrurvh"
}


def fetch_games(query):
    response = requests.post(API_URL, headers=HEADERS, data=query)
    return response.json()


queries = {
    "new_games": """
        fields name, cover.url, first_release_date;
        where first_release_date >= {last_2_months} & first_release_date <= {today};
        sort first_release_date desc;
        limit 9;
    """.format(last_2_months=int(time.time()) - 60 * 60 * 24 * 60, today=int(time.time())),

    "top_rated": """
        fields name, cover.url, rating;
        where rating > 85;
        sort rating desc;
        limit 9;
    """,

    "trending": """
        fields name, cover.url, hypes;
        where hypes > 50;
        sort hypes desc;
        limit 9;
    """
}

# Получаем данные
games_data = {category: fetch_games(query) for category, query in queries.items()}

# Теперь у нас есть:
new_games = games_data["new_games"]       # Новые игры
top_rated = games_data["top_rated"]       # Самые рейтинговые
trending = games_data["trending"]         # Трендовые игры

import json, os, requests
from dotenv import load_dotenv
from tqdm import tqdm


# ---------------- CONFIG ----------------
load_dotenv()
ENCYKOREA_API_KEY = os.getenv("ENCYKOREA_API_KEY")
ENCYKOREA_ENDPOINT_SEARCH = os.getenv("ENCYKOREA_ENDPOINT_SEARCH")
ENCYKOREA_ENDPOINT_FIELD = os.getenv("ENCYKOREA_ENDPOINT_FIELD")
ENCYKOREA_ENDPOINT_ARTICLE = os.getenv("ENCYKOREA_ENDPOINT_ARTICLE")


# ---------------- GET DATA ----------------
def fetch_from_encykorea(eids: list[str], dst_path: str, API_KEY: str) -> None:
    headers = { "X-API-Key": API_KEY }
    # params = {
    #     "keyword": "민화",
    #     "field": "예술·체육",
    #     "pageNo": 1,
    # }
    fetched = []
    for eid in tqdm(eids, desc="Fetching data from Encyclopedia of Korean Culture"):
        # response = requests.get(url=ENCYKOREA_ENDPOINT_SEARCH, params=params, headers=headers, timeout=30)
        # response = requests.get(url=ENCYKOREA_ENDPOINT_FIELD+"예술·체육", headers=headers, timeout=30)
        response = requests.get(url=ENCYKOREA_ENDPOINT_ARTICLE+eid, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        print(data.keys())

        # articles = data.get("articles")
        # print(articles[0].get("headword"))
        article = data.get("article")
        fetched.append({
            "headword": article.get("headword"),
            "body": article.get("body").replace('\r', '').split('\n', 1)[1].strip(),
        })
    with open(dst_path, "w", encoding="utf-8") as dst_file:
        json.dump(fetched, dst_file, ensure_ascii=False, indent=4)


# ---------------- MAIN ----------------
def main():
    eids = ["E0020370"]
    dst_path = "data/fetched.json"
    
    print("🔄 Fetching data from Encyclopedia of Korean Culture...")
    fetch_from_encykorea(eids, dst_path, ENCYKOREA_API_KEY)

    print("✅ Data fetching complete.")


if __name__ == "__main__":
    main()
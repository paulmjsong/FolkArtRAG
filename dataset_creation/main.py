import os
from dotenv import load_dotenv

from fetch_data import fetch_from_encykorea, fetch_from_heritage


# ---------------- CONFIG ----------------
load_dotenv()
ENCYKOREA_API_KEY = os.getenv("ENCYKOREA_API_KEY")
ENCYKOREA_ENDPOINT = os.getenv("ENCYKOREA_ENDPOINT_ARTICLE")

HERITAGE_API_KEY = os.getenv("HERITAGE_API_KEY")
HERITAGE_ENDPOINT = os.getenv("HERITAGE_ENDPOINT")


# ---------------- MAIN ----------------
def main():
    keywords = ['회화', '동물', '식물']
    src_path = "data/한국학중앙연구원_한국민족문화대백과사전_20240130.csv"
    dst_path = "data/fetched.json"
    
    if not os.path.exists(src_path):
        print(f"❗ Source file {src_path} not found. Please provide a valid source file.")
        return
    
    print("🔄 Fetching data from Encyclopedia of Korean Culture...")
    fetch_from_encykorea(src_path, dst_path, keywords, ENCYKOREA_API_KEY, ENCYKOREA_ENDPOINT)

    print("🔄 Fetching data from Korea Heritage Service...")
    fetch_from_heritage(src_path, dst_path, HERITAGE_API_KEY, HERITAGE_ENDPOINT)

    print("✅ Data fetching complete.")


if __name__ == "__main__":
    main()
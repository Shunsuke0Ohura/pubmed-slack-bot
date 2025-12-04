import os
import requests
from datetime import datetime, timedelta

SLACK_URL = os.environ["SLACK_WEBHOOK_URL"]
EMAIL = "example@example.com"   # 連絡先（何でもOK）
QUERY = "(anesthesia OR anesthesiology OR neuroscience)"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

def fetch_pubmed():
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    params = {
        "db": "pubmed",
        "term": QUERY,
        "mindate": yesterday.strftime("%Y/%m/%d"),
        "maxdate": today.strftime("%Y/%m/%d"),
        "datetype": "pdat",
        "retmax": 20
    }

    r = requests.get(BASE + "esearch.fcgi", params=params)
    ids = r.text.split("<Id>")[1:]
    ids = [x.split("</Id>")[0] for x in ids]

    if not ids:
        send_to_slack("今日は新しい論文はありません。")
        return

    msg = "*今日のPubMed新着論文*\n"
    for pmid in ids:
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        msg += f"- <{url}|PMID {pmid}>\n"

    send_to_slack(msg)

def send_to_slack(text):
    requests.post(SLACK_URL, json={"text": text})

if __name__ == "__main__":
    fetch_pubmed()

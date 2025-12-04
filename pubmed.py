import requests
import os
import time

# ========== 1) PubMed: 最新5本の PMID を検索 ==========
def search_pubmed_ids():
    query = '(anesthesia OR anesthesiology OR anesthetics OR sevoflurane OR isoflurane OR propofol OR ketamine) AND (neuroscience OR neuron OR synaptic OR hippocampus OR cortex OR axon OR "action potential" OR calcium OR sodium) AND ("last 1 day"[dp])'
    
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": 5,
        "sort": "pubdate",
        "retmode": "json"
    }
    r = requests.get(url, params=params).json()
    return r["esearchresult"].get("idlist", [])


# ========== 2) PMID → Abstract を取得 ==========
def fetch_pubmed_abstract(pmid):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml"
    }
    r = requests.get(url, params=params)
    xml = r.text

    start = xml.find("<AbstractText>")
    end = xml.find("</AbstractText>")
    if start != -1 and end != -1:
        text = xml[start+15:end]
    else:
        text = "No abstract available."
    return text


# ========== 3) OpenAI 翻訳 ==========
def translate_to_japanese(text):
    api_key = os.environ.get("OPENAI_API_KEY")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a professional biomedical translator."},
            {"role": "user", "content": f"以下の英文アブストラクトを自然な医学日本語に翻訳してください:\n\n{text}"}
        ]
    }

    r = requests.post("https://api.openai.com/v1/chat/completions",
                      headers=headers, json=data)
    return r.json()["choices"][0]["message"]["content"]


# ========== 4) Slack 通知 ==========
def send_to_slack(message):
    webhook = os.environ["SLACK_WEBHOOK_URL"]
    requests.post(webhook, json={"text": message})


# ========== 5) 実行フロー ==========
if __name__ == "__main__":

    pmids = search_pubmed_ids()

    if not pmids:
        send_to_slack("本日の該当論文はありませんでした。")
        exit()

    for pmid in pmids:
        abstract = fetch_pubmed_abstract(pmid)
        translated = translate_to_japanese(abstract)

        msg = f"📘 *PMID: {pmid}*\nhttps://pubmed.ncbi.nlm.nih.gov/{pmid}/\n\n📝 *日本語訳 Abstract*\n{translated}"
        send_to_slack(msg)

        time.sleep(2)  # API連続負荷を軽減

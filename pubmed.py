import requests
import os

# ========== 1) PubMed abstract を取得 ==========
def fetch_pubmed(pmid):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml"
    }
    r = requests.get(url, params=params)
    xml = r.text

    # Abstract の取り出し（簡易版）
    start = xml.find("<AbstractText>")
    end = xml.find("</AbstractText>")
    if start != -1 and end != -1:
        abstract = xml[start+15:end]
    else:
        abstract = "No abstract available."
    return abstract


# ========== 2) OpenAI API で日本語に翻訳 ==========
def translate_to_japanese(text):
    api_key = os.environ.get("OPENAI_API_KEY")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "gpt-4o-mini",   # 安くて翻訳が得意
        "messages": [
            {"role": "system", "content": "You are a professional medical translator."},
            {"role": "user", "content": f"以下の英文アブストラクトを専門的な日本語に翻訳してください:\n\n{text}"}
        ]
    }

    r = requests.post("https://api.openai.com/v1/chat/completions",
                      headers=headers, json=data)
    result = r.json()
    translated = result["choices"][0]["message"]["content"]
    return translated


# ========== 3) Slack に送信 ==========
def send_to_slack(message):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    payload = {"text": message}
    requests.post(webhook_url, json=payload)


# ========== 4) 実行フロー ==========
if __name__ == "__main__":
    pmid = "12345678"  # ← ここを検索した PMID に置き換える or 自動取得処理を追加

    abstract = fetch_pubmed(pmid)
    translated = translate_to_japanese(abstract)

    text = f"【PMID: {pmid}】\n\n📝 *Abstract（日本語訳）*\n{translated}"

    send_to_slack(text)

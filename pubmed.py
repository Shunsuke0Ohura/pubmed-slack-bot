import os
import requests

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

SEARCH_TERMS = '("anesthesia" OR "anesthesiology" OR "sevoflurane" OR "isoflurane" OR "neuroscience" OR "synaptic" OR "axon")'
MAX_PAPERS = 5


def fetch_pubmed():
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": SEARCH_TERMS,
        "retmax": MAX_PAPERS,
        "sort": "pub date",
        "retmode": "json"
    }
    r = requests.get(url, params=params)
    ids = r.json()["esearchresult"]["idlist"]

    papers = []

    for pmid in ids:
        detail_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        detail_params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml"
        }
        res = requests.get(detail_url, params=detail_params)
        xml = res.text

        # Title
        try:
            title = xml.split("<ArticleTitle>")[1].split("</ArticleTitle>")[0]
        except:
            title = "(No Title)"

        # Authors
        authors = []
        if "<AuthorList>" in xml:
            raw = xml.split("<AuthorList>")[1].split("</AuthorList>")[0]
            auth_blocks = raw.split("<Author")[1:]
            for ab in auth_blocks:
                try:
                    last = ab.split("<LastName>")[1].split("</LastName>")[0]
                    fore = ab.split("<ForeName>")[1].split("</ForeName>")[0]
                    authors.append(f"{fore} {last}")
                except:
                    pass
        author_text = ", ".join(authors) if authors else "(No authors)"

        # Journal
        try:
            journal = xml.split("<Journal>")[1].split("</Journal>")[0]
            journal_title = journal.split("<Title>")[1].split("</Title>")[0]
        except:
            journal_title = "(No Journal)"

        # Publication Date
        try:
            pubdate = xml.split("<PubDate>")[1].split("</PubDate>")[0]
            year = pubdate.split("<Year>")[1].split("</Year>")[0] if "<Year>" in pubdate else "----"
            month = pubdate.split("<Month>")[1].split("</Month>")[0] if "<Month>" in pubdate else "--"
            day = pubdate.split("<Day>")[1].split("</Day>")[0] if "<Day>" in pubdate else "--"
            pubdate_text = f"{year}-{month}-{day}"
        except:
            pubdate_text = "(No Date)"

        # Keywords
        keywords = []
        if "<KeywordList>" in xml:
            kw_raw = xml.split("<KeywordList>")[1].split("</KeywordList>")[0]
            kw_blocks = kw_raw.split("<Keyword")
            for k in kw_blocks[1:]:
                try:
                    kw = k.split(">")[1].split("</Keyword>")[0]
                    keywords.append(kw)
                except:
                    pass
        keyword_text = ", ".join(keywords) if keywords else "(No Keywords)"

        # Abstract
        try:
            abstract = xml.split("<AbstractText")[1].split(">")[1].split("</AbstractText>")[0]
        except:
            abstract = "(No Abstract)"

        papers.append({
            "pmid": pmid,
            "title": title,
            "authors": author_text,
            "journal": journal_title,
            "date": pubdate_text,
            "keywords": keyword_text,
            "abstract": abstract
        })

    return papers


def translate_text(text):
    """ChatGPT API を使って日本語に翻訳"""
    url = "https://api.openai.com/v1/responses"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-4o-mini",
        "input": f"Translate the following English text into natural Japanese:\n{text}"
    }

    r = requests.post(url, json=payload, headers=headers)
    data = r.json()

    # 新しいAPI形式に対応
    try:
        return data["output_text"]
    except:
        try:
            return data["output"][0]["content"][0]["text"]
        except:
            # デバッグ用
            return f"(翻訳エラー: {data})"


def send_to_slack(message):
    requests.post(SLACK_WEBHOOK_URL, json={"text": message})


def main():
    papers = fetch_pubmed()
    message = "*📰 本日の PubMed 新着論文（日本語翻訳つき）*\n"

    for p in papers:
        jp_abs = translate_text(p["abstract"])

        message += "\n---------------------------------\n"
        message += f"*タイトル*: {p['title']}\n"
        message += f"*著者*: {p['authors']}\n"
        message += f"*ジャーナル*: {p['journal']}\n"
        message += f"*出版日*: {p['date']}\n"
        message += f"*キーワード*: {p['keywords']}\n"
        message += f"*PMID*: https://pubmed.ncbi.nlm.nih.gov/{p['pmid']}/\n"
        message += f"*要旨（日本語）*:\n{jp_abs}\n"

    send_to_slack(message)
    print("Done.")


if __name__ == "__main__":
    main()

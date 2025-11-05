import os
from dotenv import load_dotenv
from datetime import datetime
from datetime import timedelta
import requests
from bs4 import BeautifulSoup

load_dotenv()

ARXIV_API = os.getenv('ARXIV_API')
class ArxivCrawler:
    def __init__(self,key_words):
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        start_time = yesterday+"0000"
        end_time = yesterday+"2359"
        self.base_url = f"http://export.arxiv.org/api/query?search_query=cat:cs.AI+AND+submittedDate:[{start_time}+TO+{end_time}]&start=0&max_results=50"#arxiv url
        self.arxiv_api = ARXIV_API
        self.download_dir = f"downloaded_papers/{yesterday}"
        self.key_words = key_words
 

    def get_paper_info(self):
        response = requests.get(self.base_url)
        soup = BeautifulSoup(response.content, 'lxml-xml')
        papers = []

        for entry in soup.find_all("entry"):
            title = entry.title.text.strip() if entry.title else ""
            abstract = entry.summary.text.strip() if entry.summary else ""

            # authors: <author><name>xxx</name></author>*
            authors = [
                a.find("name").text.strip()
                for a in entry.find_all("author")
                if a.find("name")
            ]

            # 日期：<published>2025-10-01T00:00:00Z</published>
            published = entry.published.text.strip() if entry.published else ""
            submission_date = published.split("T")[0]  # 只要 YYYY-MM-DD

        # PDF 链接：type="application/pdf"
            pdf_link = "No PDF link found"
            for link in entry.find_all("link"):
                if link.get("type") == "application/pdf":
                    pdf_link = link.get("href")
                    break

            # 关键字匹配（建议做小写匹配）
            # 大小写无关的匹配
            title_lower = title.lower()
            abstract_lower = abstract.lower()

            # 关键字是否在标题或摘要中出现
            if any(kw.lower() in title_lower or kw.lower() in abstract_lower for kw in self.key_words):
                papers.append(
                    {
                        "title": title,
                        "authors": authors,
                        "abstract": abstract,
                        "submission_date": submission_date,
                        "pdf_link": pdf_link,
                    }
                )
                print(f"✅ Paper matched: {title}")
            else:
                print("No matched paper found.")
        return papers

    def save_pdf_files(self,papers):
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        for paper in papers:
            response = requests.get(paper['pdf_link'])
            if response.status_code == 200:
                with open(os.path.join(self.download_dir, paper['title']+'.pdf'), 'wb') as f:
                    f.write(response.content)
            else:
                print(f"Failed to download {paper['title']}")
    
if __name__ == '__main__':
    crawler = ArxivCrawler(['llm','agent'])
    papers = crawler.get_paper_info()
    print(papers)
    crawler.save_pdf_files(papers)

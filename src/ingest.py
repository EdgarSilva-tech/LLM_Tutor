from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def run(playwright, url, selector):
    browser = playwright.chromium.launch()
    page = browser.new_page()
    page.goto(url)

    page_content = page.content()
    soup = BeautifulSoup(page_content, "html.parser")
    extract = [
        "https://www.khanacademy.org" + object.get("href")
        for object in soup.select("a._pkhvgz8")
    ]
    print(f"Extract: {extract}")

    for link in extract:
        page = browser.new_page()
        page.goto(link)
        link_content = page.content()
        link_html = BeautifulSoup(link_content, "html.parser")
        transcript_page = [
            "https://www.khanacademy.org" + object.get("href")
            for object in link_html.select("a._zl1qagl")
        ]
        print(f"Transcript page: {transcript_page}")

        for i, tp in enumerate(transcript_page):
            page = browser.new_page()
            page.goto(tp)
            link_content = page.content()
            link_html = BeautifulSoup(link_content, "html.parser")
            content = [
                "https://www.khanacademy.org" + object.get("href")
                for object in link_html.select("a._pkhvgz8")
            ]
            print(f"content: {content}")
            for i, n in enumerate(content):
                page = browser.new_page()
                page.goto(n)
                html_content = page.content()
                html = BeautifulSoup(html_content, "html.parser")
                extracts = [
                    el.text for el in html.select("div._1fezbb8") if el.text.strip()
                ]
                print(f"Extracts:\n{extracts}")

                if extracts != []:
                    extract = extracts[0]
                    with open(f"test_data/test_{n.split('/')[-1]}.txt", "a") as content:
                        content.write(extract)
                else:
                    continue


with sync_playwright() as playwright:
    run(playwright, "https://www.khanacademy.org/math/ap-calculus-ab", "body")

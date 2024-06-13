import requests
from bs4 import BeautifulSoup


def scrape_papers():
    url = "https://huggingface.co/papers"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    papers = []
    seen_urls = set()

    for item in soup.select('article.relative.flex.flex-col.overflow-hidden.rounded-xl.border'):
        title_tag = item.select_one('h3 a')
        video_tag = item.select_one('video')  # 비디오 태그 선택
        img_tag = item.select_one('a img')  # 이미지 태그 선택
        if title_tag and (img_tag or video_tag):
            title = title_tag.get_text(strip=True)
            link = "https://huggingface.co" + title_tag['href']
            if video_tag:  # 비디오가 있으면 비디오 URL 사용
                media_src = video_tag['src']
            else:  # 비디오가 없으면 이미지 URL 사용
                media_src = img_tag['src']
            if link not in seen_urls:
                seen_urls.add(link)
                papers.append({
                    'title': title,
                    'link': link,
                    'media': media_src  # 'image' 대신 'media' 사용
                })

    return papers

if __name__ == "__main__":
    papers = scrape_papers()
    print(papers)
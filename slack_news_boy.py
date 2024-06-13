import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from io import BytesIO
import time
from CONSTANT import slack_token, slack_channel_id

logging.basicConfig(level=logging.DEBUG)

# Slack Bot OAuth Token and Channel ID
SLACK_TOKEN = slack_token # Bot OAuth Token
SLACK_CHANNEL_ID = slack_channel_id  # Replace with your Slack Channel ID

slack_client = WebClient(token=SLACK_TOKEN)

# Store the last scraped news titles
last_scraped_titles_news = []
last_scraped_titles_paper = []

def scrape_news():
    url = "https://www.aitimes.com/news/articleList.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    articles = []
    for item in soup.select('section#section-list ul.type1 li'):
        title_tag = item.select_one('h4.titles a')
        time_tag = item.select_one('em.info.dated')

        if title_tag and time_tag:
            title = title_tag.get_text(strip=True)
            link = "https://www.aitimes.com" + title_tag['href']
            time = time_tag.get_text(strip=True)
            # Convert time to datetime object for sorting
            time_obj = datetime.strptime(time, "%m.%d %H:%M")
            articles.append({
                'title': title,
                'link': link,
                'time': time,
                'time_obj': time_obj
            })
    # Sort articles by time_obj in ascending order
    articles.sort(key=lambda x: x['time_obj'])

    return articles

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


def send_news_to_slack(articles):
    chunk_size = 20
    for i in range(0, len(articles), chunk_size):
        chunk = articles[i:i + chunk_size]
        blocks = []
        for article in chunk:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⏰: {article['time']}\n🗞️: *<{article['link']}|{article['title']}>*\n"
                }
            })
            blocks.append({"type": "divider"})

        try:
            response = slack_client.chat_postMessage(
                channel=SLACK_CHANNEL_ID,
                blocks=blocks,
                unfurl_links=False,  # 링크 미리보기 비활성화
                unfurl_media=False   # 미디어 미리보기 비활성화
            )
            logging.info(f"Message sent to Slack: {response['ts']}")
        except SlackApiError as e:
            logging.error(f"Error sending message to Slack: {e.response['error']}")


def is_media_url_valid(url):
    try:
        response = requests.head(url)
        return response.status_code == 200
    except Exception:
        return False
                

def send_papers_to_slack(papers):
    if not papers:
        return

    date_str = datetime.now().strftime("%b. %d. %Y")
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"📮 *Daily Papers [{date_str}]* 📮\n"
            }
        }
    ]

    for paper in papers:
        if not is_media_url_valid(paper['media']):
            logging.warning(f"Invalid media URL: {paper['media']}")
            continue

        if paper['media'].endswith(('png', 'jpg', 'jpeg')):
            media_block = {
                "type": "image",
                "image_url": paper['media'],
                "alt_text": paper['title']
            }
        else:
            media_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{paper['media']}|[Watch Video]>*"
                }
            }

        paper_block = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{paper['link']}|{paper['title']}>*"
                }
            },
            media_block,
            {
                "type": "divider"
            }
        ]
        blocks.extend(paper_block)

    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    block_chunks = list(chunks(blocks, 20))

    try:
        for chunk in block_chunks:
            response = slack_client.chat_postMessage(
                channel=SLACK_CHANNEL_ID,
                blocks=chunk,
                unfurl_links=False,
                unfurl_media=False
            )
            logging.info(f"Message sent to Slack: {response['ts']}")
    except SlackApiError as e:
        logging.error(f"Error sending message to Slack: {e.response['error']}")
    except Exception as e:
        logging.error(f"Error creating or sending message: {str(e)}")


def news_sender():
    global last_scraped_titles_news
    new_scraped_news = scrape_news()

    new_articles = [article for article in new_scraped_news if article['title'] not in last_scraped_titles_news]

    if new_articles:
        logging.info(f"[New!] {len(new_articles)} articles found.")
        send_news_to_slack(new_articles)
        last_scraped_titles_news = [article['title'] for article in new_scraped_news]  # 최신 기사 목록 업데이트
    else:
        logging.info("Keep waiting for another news ...")

def papers_sender():
    global last_scraped_titles_paper
    new_papers = scrape_papers()

    # 새로운 논문 중 이미 보낸 논문을 제외
    new_articles = [paper for paper in new_papers if paper['title'] not in last_scraped_titles_paper]

    if new_articles:
        logging.info(f"[New!] {len(new_articles)} papers found.")
        send_papers_to_slack(new_articles)
        last_scraped_titles_paper = [paper['title'] for paper in new_papers]  # 최신 논문 목록 업데이트
    else:
        logging.info("Keep waiting for another paper ...")


# 스케줄러 설정
scheduler = BlockingScheduler()

# 첫 실행시 바로 실행되도록 설정
# scheduler.add_job(papers_sender, 'date', run_date=datetime.now())
# scheduler.add_job(news_sender, 'date', run_date=datetime.now())

scheduler.add_job(papers_sender, 'interval', minutes=1/6)  # Check every n minutes
scheduler.add_job(news_sender, 'interval', minutes=1/6)


if __name__ == '__main__':
    try:
        logging.info("Starting news and papers sender...")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Stopping news and papers sender...")

import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
from CONSTANTS import discord_token, guild_id, channel_id
# Store the last scraped news title
last_scraped_title = ""

# Set default intent for discord client
intents = discord.Intents.default()
intents.typing = False
intents.presences = False

# Bot TOKEN, SERVER ID, CHANNEL ID
TOKEN = discord_token
GUILD_ID = guild_id
CHANNEL_ID = channel_id

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    channel = discord.utils.get(guild.text_channels, id=CHANNEL_ID)
    # Start the news scraping task if not already running
    if not news_scraper.is_running():
        news_scraper.start(channel)

@tasks.loop(minutes=1)
async def news_scraper(channel):
    global last_scraped_title
    try:
        new_news = scrape_latest_news()

        if new_news and new_news["title"] != last_scraped_title:
            await send_news(channel, new_news)
            last_scraped_title = new_news["title"]
        else:
            print("No new news found or same as last scraped news.")
    except Exception as e:
        print(f"An error occurred: {e}")

def scrape_latest_news():
    url = "https://news.hada.io/new"
    baseurl = "https://news.hada.io/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        news_container = soup.find(class_="topic_row")
        if not news_container:
            raise ValueError("Could not find the news container.")

        topictitle = news_container.find(class_="topictitle")
        topicdesc = news_container.find(class_="topicdesc")

        if not topictitle:
            raise ValueError("Could not find the news title.")

        title = topictitle.get_text(strip=True)
        link = topictitle.find("a")["href"].strip()
        link_desc = topicdesc.find("a")["href"].strip() if topicdesc else ""

        return {
            "baseurl": baseurl,
            "title": title,
            "link": link,
            "link_desc": link_desc
        }
    except requests.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while scraping: {e}")
        return None

async def send_news(channel, news):
    try:
        news_info = f'# {news["title"]}\n- 원본 링크: {news["link"]}\n- 긱뉴스 링크: {news["baseurl"] + news["link_desc"]}'
        await channel.send(news_info)
    except Exception as e:
        print(f"An error occurred while sending news: {e}")

bot.run(TOKEN)
import os
import time

import google.api_core.exceptions
import openai
import telegram
from telegram.constants import ParseMode
import asyncio

import requests as requests
from bs4 import BeautifulSoup
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from dotenv import load_dotenv
from db import save_to_db, in_db

load_dotenv()

credentials = service_account.Credentials.from_service_account_file('peppy-tiger-374003-fa5a704f0d24.json')
translater = translate.Client(credentials=credentials)

openai.api_key = os.getenv('OPENAI')
bot_token = os.getenv('BOT')

async def get_news():
    bot = telegram.Bot(token=bot_token)
    channel_id = '@CHRNV_NEWS'

    base_url = 'https://www.theblock.co'

    headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/'
          '*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)'
              ' Chrome/111.0.0.0 Safari/537.36'
    }
    response = requests.get(url=base_url+'/latest', headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    latest = soup.find('div').find_all('article')[::-1]

    for article in latest:
        link = article.find('a')['href']
        article_id = link.split('/')[2]
        art_response = requests.get(url=base_url + link, headers=headers)
        art_soup = BeautifulSoup(art_response.text, 'html.parser')
        article_title = art_soup.find(class_="articleContent").find('h1').text
        article_timestamp = art_soup.find(class_="timestamp tbcoTimestamp").text.split('\n')[1].strip('• , EDT')
        image = art_soup.find(class_="articleFeatureImage type:primaryImage").find('img')['src']
        article_content = art_soup.find(class_="quickTake").find_all('li')
        full_article = ''

        content = '\n'.join([i.text for i in article_content])
        try:
            full_article += str(content)
        except TypeError:
            # print(article_title)
            pass

        if not in_db(article_id):
            try:
                transl_title = translater.translate(article_title, target_language='ru').get('translatedText')
                translated_full_article = translater.translate(full_article, target_language='ru').get('translatedText')
            except google.api_core.exceptions.Forbidden:
                transl_title = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "assistant", "content": f'перевод {article_title}'}
                    ]
                ).choices[0]['message']['content']
                translated_full_article = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "assistant", "content": f'перевод {full_article}'}
                    ]
                ).choices[0]['message']['content']
            link_text = 'Ссылка на источник'

            message_to_tg = f'*{transl_title}*\n\n' \
                            f'{translated_full_article}\n\n' \
                            f'[{link_text}]({base_url + link})'
            await bot.send_photo(chat_id=channel_id, photo=image, caption=message_to_tg, parse_mode=ParseMode.MARKDOWN)
            save_to_db(article_title, article_id, article_timestamp, base_url + link)
        await asyncio.sleep(30)


async def main():
    """Main coroutine that runs the bot loop."""
    # try:
    while True:
        await get_news()
        await asyncio.sleep(3600)  # Pause for 2 minutes
    # except Exception as e:
    #     print(e)


if __name__ == '__main__':
    print('Start working')
    asyncio.run(main())

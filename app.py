from flask import Flask, render_template, request, session, redirect, url_for
import json
import time
import requests
from pytrends.request import TrendReq
from urllib.request import urlopen, Request
import bleach
from bs4 import BeautifulSoup
import analyzer
import vk
import datetime
from peewee import *
from threading import Thread

db = SqliteDatabase('main.db')
group_id = "-30666517"


def trends(topic):
    score = 0
    time = str(datetime.datetime.now())
    year = int(time[0:4])
    month = int(time[5:7])
    day = int(time[8:10])
    hour = int(time[11:13])
    pytrends = TrendReq(hl='ru-RU', tz=360)
    smth = \
    pytrends.get_historical_interest([topic], year_start=year, month_start=month, day_start=day - 7, hour_start=hour,
                                     year_end=year,
                                     month_end=month, day_end=day, hour_end=hour, cat=0, geo='', gprop='', sleep=0)[
        topic]
    for i in range(0, 167):
        score += smth[-i]
    score = float(score / 168)
    return score


def parsepost(post):
    pic_num = 0
    doc_num = 0
    if_poll, if_longread, text_link = None, None, None
    vid_num = 0
    links = []
    views = post['response']['items'][1]['views']['count']
    items = post['response']['items'][1]
    if 'attachments' in items[k]:
        for i in range(len(items['attachments'])):
            if items['attachments'][i]['type'] == 'photo':
                pic_num += 1
            if items['attachments'][i]['type'] == 'video':
                vid_num += 1
            if items['attachments'][i]['type'] == 'link' and 'm.vk.com/@' in items['attachments'][i]['link']['url']:
                if_longread = True
                text_link = items['attachments'][i]['link']['url']
                html = requests.get(text_link).text
                soup = BeautifulSoup(html, 'html.parser').find()
                for k in soup.find_all('a', title=True):
                    links.append(k['title'])
            if items['attachments'][i]['type'] == 'poll':
                if_poll = True
            if items['attachments'][i]['type'] == 'doc':
                doc_num += 1
    return {"pic_num": pic_num, "doc_num": doc_num, "vid_num": vid_num, "if_poll": if_poll, "if_longread": if_longread,
            "links": links, 'views': views}


def parsedoc(url):
    page = urlopen(Request(url, headers={'User-Agent': 'Mozilla'}))
    soup = BeautifulSoup(page, features="html.parser")
    for div in soup.find_all("div", {'id': "comments"}):
        div.decompose()
    for footer in soup.find_all("footer", {'id': "footer"}):
        footer.decompose()
    code = len(soup.find_all('code'))
    img = len(soup.find_all('img'))
    clean = soup.find('time')
    clean2 = soup.find('h1')
    headline2 = soup.find_all('h2')
    headlines = len(headline2)
    time = bleach.clean(str(clean), tags=[], strip=True)
    title = bleach.clean(str(clean2), tags=[], strip=True)
    return {"title": title,
            "time": time,
            "headlines": headlines,
            "img": img,
            "code": code}


class Post(Model):
    post_id = CharField()
    doc_header = CharField()
    doc_link = CharField()
    date_publish = DateField()
    post_viewers_estimated = IntegerField()
    doc_viewers_estimated = IntegerField()

    class Meta:
        database = db  # This model uses the "main.db" database.


db.connect()
db.create_tables([Post])

session = vk.Session("ef2d5debef2d5debef2d5debbaef47df34eef2def2d5debb3fbae47f8675a0656bd4369")
api = vk.API(session)


def main_worker(group_id):
    global Post, api
    while True:
        latest_post = api.wall.get(owner_id=group_id, count="2", v="5.95")
        # print(latest_post)
        post_data = parsepost(latest_post)
        if Post.select().where(Post.post_id == latest_post['items'][1]["id"]).count() == len(post_data["links"]):
            time.sleep(60)
            continue
        else:
            for link in post_data["links"]:
                if Post.select().where(Post.doc_link == link).count() != 0:
                    continue
                else:
                    doc_data = parsedoc(link)
                    current_doc = Post(post_id=latest_post['items'][1]["id"],
                                       doc_header=doc_data["title"],
                                       doc_link=link,
                                       date_publish=datetime.datetime.fromtimestamp(latest_post['items'][1]['date']),
                                       post_viewers_estimated=analyzer.checkpost(post_data),
                                       doc_viewers_estimated=analyzer.checkdoc(doc_data))
                    current_doc.save()


app = Flask(__name__)
app.secret_key = 'jrfasefasefgj'

posts_file = open('posts.json', 'r')
posts = json.loads(posts_file.read())
posts_file.close()

num_pages = len(posts) / 10

if num_pages > round(num_pages):
    num_pages = round(num_pages) + 1
else:
    num_pages = round(num_pages)


@app.route('/', methods=['GET'])
def index():
    try:
        page = int(request.args.get('page', 0))
    except:
        page = 0
    start = page * 10
    end = (page + 1) * 10
    return render_template('index.html', posts=posts[start:end], pages=num_pages)


t = Thread(target=main_worker, args=[group_id])
t.start()

app.run(debug=True, port=5000)

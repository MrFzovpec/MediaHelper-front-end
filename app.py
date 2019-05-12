from flask import Flask, render_template, request, session, redirect, url_for
import time
import requests
from random import randrange
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


def parsepost(posts):
    pic_num = 0
    doc_num = 0
    if_poll, if_longread, text_link = None, None, None
    vid_num = 0
    links = []
    rets = []
    items = posts['items']
    for k in range(len(items)):
        if "attachments" in items[k]:
            views = items[k]['views']['count']
            text = items[k]['text']
            for i in range(len(items[k]['attachments'])):
                if items[k]['attachments'][i]['type'] == 'photo':
                    pic_num += 1
                if items[k]['attachments'][i]['type'] == 'video':
                    vid_num += 1
                if items[k]['attachments'][i]['type'] == 'link' and 'm.vk.com/@' in items[k]['attachments'][i]['link'][
                    'url']:
                    if_longread = True
                    text_link = items[k]['attachments'][i]['link']['url']
                    html = requests.get(text_link).text
                    soup = BeautifulSoup(html, 'html.parser').find()
                    for f in soup.find_all('a', title=True):
                        if f["title"] != "https://tproger.ru/":
                            links.append(f['title'])
                if items[k]['attachments'][i]['type'] == 'poll':
                    if_poll = True
                if items[k]['attachments'][i]['type'] == 'doc':
                    doc_num += 1
                ret = {"pic_num": pic_num,
                       "doc_num": doc_num,
                       "vid_num": vid_num,
                       "if_poll": if_poll,
                       "if_longread": if_longread,
                       "links": links,
                       'views': views,
                       "text": text}
                rets.append(ret)
    return rets


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
    div = soup.find('div', {'class': "entry-content"})
    OUT_TEXT = str(div).split('<h2>')
    par = OUT_TEXT[0].split('<p>')
    par2 = []
    for i in par:
        if '</p>' in i:
            clean = bleach.clean(i, tags=[], strip=True)
            par2.append(clean)
    content = ' '.join(par2)
    return {"title": title,
            "time": time,
            "headlines": headlines,
            "img": img,
            "code": code,
            "content": content}


class Post(Model):
    post_id = CharField()
    post_text = CharField()
    doc_header = CharField()
    doc_link = CharField()
    date_publish = DateField()
    post_viewers_estimated = IntegerField()
    doc_viewers_estimated = IntegerField()

    class Meta:
        database = db  # This model uses the "main.db" database.


db.connect()
db.create_tables([Post])

session = vk.Session("1d1bfc251d1bfc251d1bfc25711d7179af11d1b1d1bfc2541cc153bc247feb77367395e")
api = vk.API(session)


def main_worker(group_id):
    global Post, api
    while True:
        latest_post = api.wall.get(owner_id=group_id, count="2", v="5.95")
        post_data = parsepost(latest_post)[1]
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
                                       post_text=doc_data["content"],
                                       doc_header=doc_data["title"],
                                       doc_link=link,
                                       date_publish=datetime.datetime.fromtimestamp(latest_post['items'][1]['date']),
                                       post_viewers_estimated=-1,
                                       doc_viewers_estimated=int(analyzer.checkdoc(doc_data) +
                                                                 analyzer.checkpost(post_data)/2))
                    current_doc.save()
            time.sleep(60)


app = Flask(__name__)
app.secret_key = 'jrfasefasefgj'

size = Post.select().count()
num_pages = size / 10

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
    posts_list = []
    statuses = ['GOOD', 'NOT GOOD', 'SUCCSESS']
    for post in Post.select().offset(start).limit(10):
        posts_list.append({
            'title': post.doc_header,
            'text': post.post_text,
            'date': post.date_publish,
            'rating': post.doc_viewers_estimated,
            'link': post.doc_link,
            'status': statuses[randrange(0,3)]
        })
    return render_template('index.html', posts=posts_list, pages=num_pages)


t = Thread(target=main_worker, args=[group_id])
t.start()

app.run(debug=True, port=5000)

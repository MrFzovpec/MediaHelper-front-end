import datetime
import time
from threading import Thread

<<<<<<< HEAD
import requests

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
                        if not "tproger.ru" in f['title']:
                            continue
                        else:
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
    page = requests.get(url, headers={'User-Agent': 'Mozilla'}).text
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
    clean3 = None

    for i in par:
        if '</p>' in i:
            clean3 = bleach.clean(i, tags=[], strip=True)
            if clean3 != "":
                try:
                    clean3 = clean3.replace('\xa0', ' ')
                except:
                    pass
                break
    content = clean3
    img2 = soup.find_all('img', src=True)
    img3 = []
    for i in img2:
        if 'https://cdn.tproger.ru/wp-content/uploads' in i['src']:
            img3.append(i['src'])
    try:
        img_link = img3[0]
    except:
        img_link = 'https://cdn.tproger.ru/wp-content/uploads/2016/06/tpbooksmini.jpg'
    print(code)
    return {"title": title,
            "time": time,
            "headlines": headlines,
            "img": img,
            "code": code,
            "content": content,
            "img_link": img_link}
=======
import vk
from flask import Flask, render_template, request
from peewee import Model, CharField, DateField, IntegerField, SqliteDatabase

import analyzer
from parsers import parsedoc, parsepost

DATABASE = SqliteDatabase('main.DATABASE')
GROUP_ID = "-30666517"
>>>>>>> 901f19d771d6b7acdca2ffed064f9267c7697502


class Post(Model):
    """
    Model for peewee database, one line per text on tproger.com
    post_id - string to get data about from what post we got the article
    doc_text - first paragraph of article for frontend
    doc_header - header of article for frontend
    doc_link - link to original article for frontend
    pic_link - link to picture from article for frontend
    date_publish - date of post's publishment, converted from unixtime from VK's API
    post_viewers_estimated - unused field. We had no time to re-develop DB structure, should do it later
    doc_viewers_extimated - estimated viewers for article, based on models predictions for post's and article's viewers
    """
    post_id = CharField()
    doc_text = CharField()
    doc_header = CharField()
    doc_link = CharField()
    pic_link = CharField()
    date_publish = DateField()
    post_viewers_estimated = IntegerField()
    doc_viewers_estimated = IntegerField()

    class Meta:
        database = DATABASE  # This model uses the "main.DATABASE" database.


DATABASE.connect()
DATABASE.create_tables([Post])

SESSION = vk.Session(
    "1d1bfc251d1bfc251d1bfc25711d7179af11d1b1d1bfc2541cc153bc247feb77367395e")
VK_API_SESSION = vk.API(SESSION)


def main_worker():
    while True:
        latest_post = VK_API_SESSION.wall.get(
            owner_id=GROUP_ID, count="2", v="5.95")
        raw_data = parsepost(latest_post)
        post_data = raw_data[1]
        if Post.select().where(Post.post_id == latest_post['items'][1]["id"]).count() >= len(post_data["links"]):
            time.sleep(60)
            continue
        else:
            for link in post_data["links"]:
                if Post.select().where(Post.doc_link == link).count() != 0:
                    continue
                else:
                    doc_data = parsedoc(link)
                    current_doc = Post(post_id=latest_post['items'][1]["id"],
                                       doc_text=doc_data["content"],
                                       doc_header=doc_data["title"],
                                       doc_link=link,
                                       pic_link=doc_data["img_link"],
                                       date_publish=datetime.datetime.fromtimestamp(
                                           latest_post['items'][1]['date']),
                                       post_viewers_estimated=-1,  # WTF? We should definately rewrite database structure
                                       doc_viewers_estimated=int(analyzer.checkdoc(doc_data) +
                                                                 analyzer.checkpost(post_data) / 2))
                    if not Post.select().where(Post.doc_link == link).exists():
                        current_doc.save()
            time.sleep(120)


app = Flask(__name__)
app.secret_key = 'jrfasefasefgj'


@app.route('/', methods=['GET'])
def index():
    size = Post.select().count()
    num_pages = size / 10

    if num_pages > round(num_pages):
        num_pages = round(num_pages) + 1
    else:
        num_pages = round(num_pages)
    stn = ""
    stp = ""

    try:
        page = int(request.args.get('page', 0))
    except:
        page = 0
    start = page * 10
    posts_list = []
    for post in Post.select().offset(start).limit(10):
        post = {
            'title': post.doc_header,
            'text': post.doc_text,
            'date': post.date_publish,
            'rating': post.doc_viewers_estimated,
            'link': post.doc_link,
            'status': '',
            'image': post.pic_link
        }
        if post['rating'] < 20000:
            post['status'] = 'NOT GOOD'
        elif post['rating'] >= 20000:
            if post['rating'] >= 50000:
                post['status'] = 'SUCCESS'
            else:
                post['status'] = 'GOOD'
        if post['title'].lower() == 'none':
            post['title'] = ''
        if (post['title'] == '') and (post['text'] == ''):
            pass
        else:
            posts_list.append(post)

    if page + 1 >= num_pages:
        stn = 'disabled'
    if page == 0:
        stp = 'disabled'
    if num_pages <= 1:
        nvs = False
    else:
        nvs = True

    return render_template(
        'index.html',
        posts=posts_list,
        pages=num_pages,
        page=page,
        status_next=stn,
        status_prev=stp,
        nav_status=nvs)


worker_thread = Thread(target=main_worker)
worker_thread.start()

app.run(debug=True, port=8080, host='0.0.0.0')

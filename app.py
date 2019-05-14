import datetime
import time
from threading import Thread

import vk
from flask import Flask, render_template, request, session
from peewee import Model, CharField, DateField, IntegerField, SqliteDatabase

import analyzer
from parsers import parsedoc, parsepost

db = SqliteDatabase('main.db')
group_id = "-30666517"


class Post(Model):
    post_id = CharField()
    post_text = CharField()
    doc_header = CharField()
    doc_link = CharField()
    pic_link = CharField()
    date_publish = DateField()
    post_viewers_estimated = IntegerField()
    doc_viewers_estimated = IntegerField()

    class Meta:
        database = db  # This model uses the "main.db" database.


db.connect()
db.create_tables([Post])

session = vk.Session(
    "1d1bfc251d1bfc251d1bfc25711d7179af11d1b1d1bfc2541cc153bc247feb77367395e")
api = vk.API(session)


def main_worker():
    while True:
        latest_post = api.wall.get(owner_id=group_id, count="2", v="5.95")
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
                                       post_text=doc_data["content"],
                                       doc_header=doc_data["title"],
                                       doc_link=link,
                                       pic_link=doc_data["img_link"],
                                       date_publish=datetime.datetime.fromtimestamp(
                                           latest_post['items'][1]['date']),
                                       post_viewers_estimated=-1,
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
            'text': post.post_text,
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

    return render_template('index.html', posts=posts_list, pages=num_pages, page=page, status_next=stn, status_prev=stp, nav_status=nvs)


t = Thread(target=main_worker, args=[group_id])
t.start()

app.run(debug=False, port=8080, host='0.0.0.0')

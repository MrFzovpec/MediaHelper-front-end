from flask import Flask, render_template, request, session, redirect, url_for
import json
import parser
import time
import analyzer
import vk
import datetime
from peewee import *
from threading import Thread

db = SqliteDatabase('main.db')
group_id = "-30666517"

def makedate(str_date):
    return datetime.date(1, 1, 1)


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

session = vk.Session("aa22c986aa22c986aa22c9865caa484959aaa22aa22c986f6f45353aaf11232557bca25")
api = vk.API(session)

def main_worker(group_id):
    global Post, api
    while True:
        latest_post = api.wall.get(owner_id=group_id, count="1", v="5.95")
        file = open('file.txt', 'w')
        post_data = parser.parsepost(latest_post)
        file.write(str(post_data))
        file.close()
        if Post.select().where(Post.post_id == latest_post['items'][0]["id"]).count() == len(post_data["links"]):
            time.sleep(60)
            continue
        else:
            for link in post_data["links"]:
                if Post.select().where(Post.doc_link == link).count() != 0:
                    continue
                else:
                    doc_data = parser.parsedoc()
                    current_doc = Post(post_id=latest_post['items'][0]["id"],
                                       doc_header=doc_data["header"],
                                       doc_link=link,
                                       date_publish=makedate(doc_data["date_publish"]),
                                       post_viewers_estimated=analyzer.checkpost(post_data),
                                       doc_viewers_estimated=analyzer.checkdoc(doc_data))
                    current_doc.save()

app = Flask(__name__)
app.secret_key = 'jrfasefasefgj'

posts_file = open('posts.json', 'r')
posts = json.loads(posts_file.read())
posts_file.close()

num_pages = len(posts)/10

if num_pages > round(num_pages):
    num_pages = round(num_pages)+1
else:
    num_pages = round(num_pages)


@app.route('/', methods=['GET'])
def index():
    try:
        page = int(request.args.get('page', 0))
    except:
        page = 0
    start = page*10
    end = (page+1)*10
    return render_template('index.html', posts=posts[start:end], pages=num_pages)

t = Thread(target=main_worker(group_id))
t.start()

app.run(debug=True, port=8080)


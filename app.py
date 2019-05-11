from flask import Flask, render_template, request, session, redirect, url_for
import json
import datetime


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
print(num_pages)

@app.route('/', methods=['GET'])
def index():
    try:
        page = int(request.args.get('page', 0))
    except:
        page = 0
    start = page*10
    end = (page+1)*10
    return render_template('index.html', posts=posts[start:end], pages=num_pages)

app.run(debug=True, port=8080)

import requests
from urllib.request import urlopen, Request
import bleach
from bs4 import BeautifulSoup

class parsers():
    @staticmethod
    def parsepost(post):
        pic_num = 0
        doc_num = 0
        if_poll, if_longread, text_link = None, None, None
        vid_num = 0
        if_poll = False
        if_longread = False
        links = []
        items = post['items'][0]
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
        return {"pic_num": pic_num, "doc_num": doc_num, "vid_num": vid_num, "if_poll": if_poll,
                "if_longread": if_longread, "links": links}

    @staticmethod
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
        return {"title": title, "time": time, "headlines": headlines, "img": img, "code": code}

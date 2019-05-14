import requests
import bleach
from bs4 import BeautifulSoup


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
    clean3 = ''
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
    return {"title": title,
            "time": time,
            "headlines": headlines,
            "img": img,
            "code": code,
            "content": content,
            "img_link": img_link}

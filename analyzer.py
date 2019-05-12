from pytrends.request import TrendReq
import datetime
import pandas as pd
import regex as re
from catboost import CatBoostRegressor, Pool

post_model = CatBoostRegressor()
doc_model = CatBoostRegressor()

post_model.load_model("models/posts_model")
doc_model.load_model("models/doc_model")


def trends(topic):
    score = 0
    time = str(datetime.datetime.now())
    year = int(time[0:4])
    month = int(time[5:7])
    day = int(time[8:10])
    hour = int(time[11:13])
    pytrends = TrendReq(hl='ru-RU', tz=360)
    smth = \
        pytrends.get_historical_interest([topic], year_start=year, month_start=month, day_start=day - 7,
                                         hour_start=hour,
                                         year_end=year,
                                         month_end=month, day_end=day, hour_end=hour, cat=0, geo='', gprop='', sleep=0)[
            topic]
    for i in range(0, 167):
        score += smth[-i]
    score = float(score / 168)
    return score


def magic(title, cache):
    points = 0
    words = title.split()
    to_trends = []
    for word in words:
        if word[0].isupper():
            to_trends.append(word)
    for word in to_trends:
        word = re.sub(r"[!.,:;»?]+$", '', word)
        if word in cache:
            points += cache[word]
            continue
        try:
            cache[word] = trends(word)
            points += cache[word]
        except:
            cache[word] = 0
            continue
    if len(to_trends) != 0:
        return points / len(to_trends)
    else:
        return 0


def checkpost(post_data):
    global post_model
    kostil = pd.DataFrame([
        {"doc_num": post_data["doc_num"],
         "if_longread": post_data["if_longread"],
         "if_poll": post_data["if_poll"],
         "pic_num": post_data["pic_num"],
         "vid_num": post_data["vid_num"],
         "links_count": len(post_data["links"])}])
    return post_model.predict(kostil)[0]


def checkdoc(doc_data):
    cache = {}
    global doc_model
    thing = magic(doc_data["title"], cache)
    kostil = pd.DataFrame([
        {"code": doc_data["code"],
         "headlines": doc_data["headlines"],
         "img": doc_data["img"],
         "trends": thing}])
    return doc_model.predict(kostil)[0]

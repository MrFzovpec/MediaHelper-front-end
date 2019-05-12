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


def magic(title):
    global cache
    points = 0
    words = title.split()
    to_trends = []
    for word in words:
        if word[0].isupper():
            to_trends.append(word)
    for word in to_trends:
        word = re.sub(r"[!.,:;»?]+$", '', word)
        print(word)
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
    return 100_000_000


def checkdoc(doc_data):
    return 100_000_000

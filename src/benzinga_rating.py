import arrow
import csv
import json
import os
import re
import requests
import sys
from bs4 import BeautifulSoup


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BENZINGA_URL = 'https://www.benzinga.com/quote/{}'
DAYS_LIMIT = 180


def fetch_stock_quote(quote):
    url = BENZINGA_URL.format(quote)
    resp = requests.get(url)
    print("Get quote: %s\n" % quote)
    if resp.status_code != 200:
        print("Failed to fetch quote: ", quote)
        return None

    html = resp.text
    # Get quote data
    data = re.search('"richQuoteData":.*?}', html)
    data = data.group(0)
    data = json.loads('{%s}' % data)
    data = data['richQuoteData']
    price = data['lastTradePrice']
    ylow = data['fiftyTwoWeekLow']
    yhigh = data['fiftyTwoWeekHigh']

    # Get all ratings in recent 6 months
    ratings = re.search('"ratings":.*?]', html)
    ratings = ratings.group(0)
    # print("current rating: \n", ratings)
    ratings = json.loads('{%s}' % ratings)
    ratingList = ratings['ratings']
    analysts = set()
    now = arrow.now()
    count = 0
    avg = 0
    top = 0
    total = 0
    for rating in ratingList:
        analyst = rating.get('analyst')
        if analyst in analysts:
            continue
        analysts.add(analyst)
        when = arrow.get(rating['date'])
        delta = now - when
        if delta.days > DAYS_LIMIT or not rating['pt_current']:
            continue
        count += 1
        val = float(rating['pt_current'])
        if val > top:
            top = val
        total += val

    if count > 0:
        avg = round(total/count, 2)
    return (quote, price, ylow, yhigh, avg, top)


def main(filename=None):
    fn = filename or 'stock_list.csv'
    file_path = os.path.join(BASE_DIR, f'./data/{fn}')
    quotes = []
    data = []

    with open(file_path, 'r') as fd:
        reader = csv.reader(fd)
        for row in reader:
            if not row:
                continue
            quote = row[0]
            quotes.append(quote)

    for quote in quotes:
        try:
            item = fetch_stock_quote(quote)
        except Exception as err:
            print("Error: ", err)
            continue
        if not item:
            continue
        data.append(item)
        # time.sleep(random.random())

    data.sort(key=lambda x: x[5], reverse=True)
    with open(file_path, 'w') as fd:
        writer = csv.writer(fd)
        for row in data:
            writer.writerow(row)

if __name__ == '__main__':
    fn = None
    if len(sys.argv) > 1:
        fn = sys.argv[1]
    main(fn)
    # print(fetch_stock_quote('TPX'))

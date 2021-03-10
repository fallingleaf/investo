import csv
import json
import os
import re
import requests


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
YAHOO_URL = 'https://finance.yahoo.com/quote/{}'


def _translate(text, key):
    text = text.group(0)
    js = json.loads('{%s}' % text)
    return float(js[key].get('raw', 0))


def fetch_stock_quote(quote):
    url = YAHOO_URL.format(quote)
    resp = requests.get(url)
    print("Get quote: %s\n" % quote)
    if resp.status_code != 200:
        print("Failed to fetch quote: ", quote)
        return None

    html = resp.text
    current = re.search('"currentPrice":.*?}', html)
    median = re.search('"targetMedianPrice":.*?}', html)
    high = re.search('"targetHighPrice":.*?}', html)

    if current and median and high:
        current = _translate(current, 'currentPrice')
        median = _translate(median, 'targetMedianPrice')
        high = _translate(high, 'targetHighPrice')
        avg_return = round((median - current) * 100 / current, 2)
        high_return = round((high - current) * 100 / current, 2)
        return (quote, current, median, high, avg_return, high_return)
    return None

def main():
    file_path = os.path.join(BASE_DIR, './data/stock_list.csv')
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
        item = fetch_stock_quote(quote)
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
    main()

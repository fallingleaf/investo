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
    # There are multiple points for 52 week ranges, ensure it's expected quote
    oneyear = re.search('"%s":.*?fiftyTwoWeekRange.*?}' % quote, html)

    surprise = 0.0
    earnings = re.search('"earningsChart":.*?\[.*?\]', html)
    if earnings:
        earnings = earnings.group(0)
        earnings = json.loads('{%s}}' % earnings)
        quarterly = earnings['earningsChart']['quarterly']
        if quarterly:
            last = quarterly[-1]
            actual, estimate = last.get('actual', {}), last.get('estimate', {})
            actual, estimate = actual.get('raw', 0), estimate.get('raw', 0)
            if estimate != 0:
                if actual < estimate:
                    surprise = -abs((estimate - actual)/estimate*100)
                if actual > estimate:
                    surprise = abs((estimate - actual)/estimate*100)

    if current and median and high and oneyear:
        current = _translate(current, 'currentPrice')
        median = _translate(median, 'targetMedianPrice')
        high = _translate(high, 'targetHighPrice')

        oneyear = oneyear.group(0)
        oneyear = json.loads('{%s}}' % oneyear)
        oneyear = oneyear.get(quote, {}).get('fiftyTwoWeekRange', {}).get('raw', '')
        ylow, yhigh = oneyear.split('-')
        ylow, yhigh = float(ylow), float(yhigh)

        return (quote, current, ylow, yhigh, median, high, round(surprise, 2))
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

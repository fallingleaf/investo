import csv
import os
import random
import requests
import time
from bs4 import BeautifulSoup


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BENZINGA_URL = 'https://www.benzinga.com/stock/{}/ratings'


def fetch_stock_quote(quote):
    url = BENZINGA_URL.format(quote.lower())
    resp = requests.get(url)
    print("Get quote: %s\n" % quote)
    if resp.status_code != 200:
        print("Failed to fetch quote: ", quote)
        return None

    html = resp.text
    selector = BeautifulSoup(html, 'html.parser')

    # Get current stock price
    title = selector.find('div', class_='stock-page-title-ticker')
    price = title.contents[0].string
    price = float(price.replace(',', ''))

    # Get all ratings
    ratings = []
    table = selector.find('table', class_='stock-ratings-calendar')
    for tr in table.tbody.find_all('tr'):
        tds = tr.find_all('td')
        info = tds[4].string
        if not info:
            continue
        ratings.append(float(info.replace(',', '')))

    if not ratings:
        return None

    ratings.sort()
    highest = ratings[-1]
    highest_return = (highest - price)*100/price
    avg = sum(ratings)/len(ratings)
    avg_return = (avg - price)*100/price
    return (quote,
            price,
            round(avg, 2),
            highest,
            round(avg_return, 2),
            round(highest_return, 2)
            )

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

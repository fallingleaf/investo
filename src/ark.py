import arrow
import csv
import heapq
import os
import requests
import tabula

from collections import defaultdict
from operator import itemgetter


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ETF = (
    ('arkk', 'https://ark-funds.com/wp-content/fundsiteliterature/holdings/ARK_INNOVATION_ETF_ARKK_HOLDINGS.pdf'),
    ('arkw', 'https://ark-funds.com/wp-content/fundsiteliterature/holdings/ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS.pdf'),
    ('arkf', 'https://ark-funds.com/wp-content/fundsiteliterature/holdings/ARK_FINTECH_INNOVATION_ETF_ARKF_HOLDINGS.pdf'),
    ('arkq', 'https://ark-funds.com/wp-content/fundsiteliterature/holdings/ARK_AUTONOMOUS_TECHNOLOGY_&_ROBOTICS_ETF_ARKQ_HOLDINGS.pdf'),
)


def parse_pdf(name, url):
    filename = f'/tmp/{name}.pdf'
    headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        raise Exception('Failed to fetch pdf: ', url)

    with open(filename, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)

    data_frames = tabula.read_pdf(filename, guess=False, pages="1")
    data = data_frames[0]
    for row in data.values:
        arr = row.tolist()
        name, sticker, shares = str(arr[3]), str(arr[5]), str(arr[11])
        if sticker == 'nan':
            continue
        shares = float(shares.replace(',', ''))
        yield (sticker, shares)


def write_csv(filename, data):
    with open(filename, 'w') as fd:
        writer = csv.writer(fd, delimiter=',')
        for row in data:
            writer.writerow(row)


def read_csv(filename):
    with open(filename, 'r') as fd:
        reader = csv.reader(fd, delimiter=',')
        for row in reader:
            if not row:
                continue
            yield row


def report(num_stock):
    stocks = defaultdict(float)

    for name, url in ETF:
        data = parse_pdf(name, url)
        for (sticker, shares) in data:
            stocks[sticker] += shares
    # Read old data
    report = os.path.join(BASE_DIR, './data/ark.csv')
    records = {}
    for row in read_csv(report):
        sticker, shares = row
        records[sticker] = float(shares)

    # Save new stock list
    write_csv(report, stocks.items())
    # Report
    purchases = []
    sold = []
    reduces = []
    increases = []

    for (sticker, shares) in stocks.items():
        if sticker not in records:
            purchases.append((sticker, shares))
        else:
            prev = records[sticker]
            if shares > prev:
                increses.append((sticker, shares - prev))
            if shares < prev:
                reduces.append((sticker, prev - shares))
            records.pop(sticker)

    for (sticker, shares) in records:
        sold.append((sticker, shares))

    purchases.sort(key=itemgetter(1), reverse=True)
    sold.sort(key=itemgetter(1), reverse=True)
    reduces.sort(key=itemgetter(1), reverse=True)
    increases.sort(key=itemgetter(1), reverse=True)

    with open(os.path.join(BASE_DIR, f'./data/ark_result.txt'), 'w') as f:
        print("ARK invest activity report on date %s" % arrow.now().date(), file=f)
        print("New stock purchases:", file=f)
        for (sticker, shares) in purchases[:num_stock]:
            print("%s:\t\t%s" % (sticker, shares), file=f)

        print("\n Sold stocks:", file=f)
        for (sticker, shares) in sold[:num_stock]:
            print("%s:\t\t%s" % (sticker, shares), file=f)

        print("\n Increase stock position:", file=f)
        for (sticker, shares) in increases[:num_stock]:
            print("%s:\t\t%s" % (sticker, shares), file=f)

        print("\n Share sold:", file=f)
        for (sticker, shares) in sold[:num_stock]:
            print("%s:\t\t%s" % (sticker, shares), file=f)

if __name__ == '__main__':
    report(10)

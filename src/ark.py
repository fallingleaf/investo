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
    r = requests.get(url, stream=True)
    with open(filename, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)

    data_frames = tabula.read_pdf(filename, pages="1")
    data = data_frames[0]
    for row in data.values:
        arr = row.tolist()
        name, sticker, shares = str(arr[3]), str(arr[5]), str(arr[11])
        if sticker == 'nan':
            continue
        shares = float(shares.replace(',', ''))
        yield (name, sticker, shares)


def write_csv(filename, data):
    with open(filename, 'w') as fd:
        writer = csv.writer(fd, delimiter=',')
        for row in data:
            writer.writerow(row)


def read_csv(filename):
    with open(filename, 'r') as fd:
        reader = csv.reader(fd, delimiter=',')
        for row in reader:
            yield row


def update_stocks(name, url, report):
    filename = os.path.join(BASE_DIR, f'./data/{name}.csv')
    records = {}
    print("Fetching new stock list for ETF: ", name)
    data = parse_pdf(name, url)
    stocks = [item for item in data]

    if os.path.exists(filename):
        for row in read_csv(filename):
            (_, sticker, _) = row
            records[sticker] = row
        print("Compare to previous stocks holding...")
        for (name, sticker, shares) in stocks:
            delta = 0
            if sticker in records:
                delta = shares - float(records[sticker][2])
                records.pop(sticker)
            else:
                report['new'][sticker] += shares
            if delta > 0:
                report['increase'][sticker] += delta
            elif delta < 0:
                report['reduce'][sticker] -= delta

        for (name, sticker, shares) in records:
            report['sold'][sticker] += shares
    print("Save new data to file...\n")
    write_csv(filename, stocks)


def report(num_stock):
    report = {
        'new': defaultdict(float),
        'increase': defaultdict(float),
        'reduce': defaultdict(float),
        'sold': defaultdict(float)
    }

    for name, url in ETF:
        update_stocks(name, url, report)

    # Report new share purchases
    print("New purchases....\n")
    new_purchases = heapq.nlargest(num_stock, report['new'].items(),
                                  key=itemgetter(1))
    for sticker, shares in new_purchases:
        print("%s:\t%s" % (sticker, shares))

    # Report share sold
    print("Share sold....\n")
    sold = heapq.nlargest(num_stock, report['sold'].items(), key=itemgetter(1))
    for sticker, shares in sold:
        print("%s:\t%s" % (sticker, shares))

    # Report increased holding
    print("Increase share holding....\n")
    increase = heapq.nlargest(num_stock, report['increase'].items(),
                              key=itemgetter(1))
    for sticker, shares in increase:
        print("%s:\t%s" % (sticker, shares))

    # Report reduce holding
    print("Reduce share holding....\n")
    reduced_shares = heapq.nlargest(num_stock, report['reduce'].items(),
                              key=itemgetter(1))
    for sticker, shares in reduced_shares:
        print("%s:\t%s" % (sticker, shares))



if __name__ == '__main__':
    report(10)

import csv
import os
import requests

import tabula

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
        name, sticker, shares = str(arr[3]), str(arr[5]), str(arr[9])
        if sticker == 'nan':
            continue
        shares = int(shares.replace(',', ''))
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


def update_stocks(name, url):
    filename = os.path.join(BASE_DIR, f'./data/{name}.csv')
    records = {}
    print("Fetching new stock list for ETF: ", name)
    data = parse_pdf(name, url)
    stocks = [item for item in data]

    if os.path.exists(filename):
        for row in read_csv(filename):
            (_, sticker, _) = row
            records[sticker] = row

        for (name, sticker, shares) in stocks:
            delta = shares
            if sticker in records:
                delta = shares - int(records[sticker][2])
                records.pop(sticker)
            if delta > 0:
                print("New share purchases: %s\t%s\t%s" % (name, sticker, delta))
            elif delta < 0:
                print("Share sold: %s\t%s\t%s" % (name, sticker, -delta))

        for (name, sticker, shares) in records:
            print("Sold all shares: %s\t%s\t%s" % (name, sticker, shares))
    print("Save new data to file...")
    write_csv(filename, stocks)


if __name__ == '__main__':
    for name, url in ETF:
        update_stocks(name, url)

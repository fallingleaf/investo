Ark ETF position scanning script
==================================

Python script used to crawl all stock positions in ETFs: ARKK, ARKQ, ARKW, ARKF
and compare the difference in holdings to previous date. It will print out which stocks are recently bought, sold or closed by ARK.

## How to use it

- Require Python 3 packages: requests, tabula-py
- Run script:
> virtualenv --python=python3.6 env
>
> . env/bin/activate
> pip install -r requirements.txt
>
> python src/ark.py

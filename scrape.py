from __future__ import division

from yahoo_fin import stock_info as si
from bs4 import BeautifulSoup
import pandas as pd
import requests
import json
import sys

def extract_profile(share):
	profile = {}
	try:
		page = requests.get('https://au.finance.yahoo.com/quote/'+share+'/profile')
		soup = BeautifulSoup(page.content, 'html.parser')
		profile['company_name'] = soup.find_all('h3')[0].get_text()
		profile['sector'] = soup.find_all('span', class_='Fw(600)')[0].get_text()
		profile['industry'] = soup.find_all('span', class_='Fw(600)')[1].get_text()
	except:
		pass
	return profile

shares = [line.strip() for line in open("/home/gerson/projects/shares/shares.txt", 'r')]

i = 0
prev_prog = ''

failures = []
successes = []
for share in shares:

	try:
		st = si.get_stats(share)
		inc = si.get_income_statement(share)
		price = si.get_live_price(share)
		bs = si.get_balance_sheet(share)
		cf = si.get_cash_flow(share)
		
		st.to_csv('/home/gerson/projects/shares/data/stats_%s.csv' % share, index=False)
		inc.to_csv('/home/gerson/projects/shares/data/income_%s.csv' % share, index=False)
		bs.to_csv('/home/gerson/projects/shares/data/balancesheet_%s.csv' % share, index=False)
		cf.to_csv('/home/gerson/projects/shares/data/cashflow_%s.csv' % share, index=False)
		with open('/home/gerson/projects/shares/data/price_%s.txt' % share, 'w') as file:
			file.write(str(price))
		with open('/home/gerson/projects/shares/data/profile_%s.json' % share, 'w') as file:
			json.dump(extract_profile(share), file)

		successes.append(share)
	except:
		failures.append(share)

	# progress
	i+=1
	progress = '%.2f' % ((i/len(shares))*100)
	if progress != prev_prog:
		print (progress + "%")
	prev_prog = progress

with open('/home/gerson/projects/shares/failures.txt', 'w') as f:
    for item in failures:
        f.write("%s\n" % item)

with open('/home/gerson/projects/shares/successes.txt', 'w') as f:
    for item in successes:
        f.write("%s\n" % item)

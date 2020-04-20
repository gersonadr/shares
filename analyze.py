from __future__ import division

from decimal import Decimal
import pandas as pd
import json
import sys
import re

d = {'K':3,'k':3,'m':6,'M':6,'b':9,'B':9}

def text_to_num(text):
	if text[-1] in d:
		num, magnitude = text[:-1], text[-1]
		return Decimal(num) * 10 ** d[magnitude]
	else:
		return Decimal(text)

shares = [line.strip() for line in open("/home/gerson/projects/shares/shares.txt", 'r')]

# be profitable
# generate cash
# earnings before interest and tax (more important in balance sheet)
# also compounding of that earnings per book value per share is far better indicator companies ability

# bloomberg machine
#  - all companies in the world
#  - reduce to north america, western europe, aus/nz
#  - financially solvent, iow, "current ratio" at least 1
#  - remove all finance related (mortgages, banks, insurance, etc)
#  - remove all tech related <------ (gerson)
#  - remove more than 10B market cap and under 100M market cap
#  - pay dividend of more than 1 cent per share
#  - debt to equity ratio of no more than X
#  - (goal is to end up with 250)

# https://saetacapital.com/2018/06/10/notes-from-anthony-deden-interview-by-grant-williams/

result = {}
result['blacklisted'] = 0
result['insolvent'] = 0
result['too_small'] = 0
result['too_big'] = 0
result['no_dividends'] = 0
result['no_income'] = 0
result['no_cash'] = 0
result['passed'] = 0

AX = True
US = True
EU = True
BR = False
HK = False
JP = False

for share in shares:
	
	if (not AX and '.AX' in share) or (not EU and '.L' in share) or (not BR and '.SA' in share) or (not HK and '.HK' in share) or (not JP and '.T' in share):
		continue 

	reject = False

	total_liabilities = sys.maxsize
	short_term_liabilities = sys.maxsize
	total_cash = 0
	total_assets = 0
	intangible_assets = 0
	shares_outstanding = sys.maxsize
	income_before_covid = 0
	market_cap = 0
	income_before_covid = 0
	has_dividends = False
	net_income = 0
	dividend = 0
	profile = {}
	price = sys.maxsize

	try:
		st = pd.read_csv('/home/gerson/projects/shares/data/stats_%s.csv' % share)
		price = float(open('/home/gerson/projects/shares/data/price_%s.txt' % share).readlines()[0])
		bs = pd.read_csv('/home/gerson/projects/shares/data/balancesheet_%s.csv' % share)
		cf = pd.read_csv('/home/gerson/projects/shares/data/cashflow_%s.csv' % share)
		inc = pd.read_csv('/home/gerson/projects/shares/data/income_%s.csv' % share)
		with open('/home/gerson/projects/shares/data/profile_%s.json' % share) as f:
			profile = json.load(f)

		#calculate
		try:
			market_cap = text_to_num(str(st.query('`Attribute`.str.startswith("Market Cap")').iloc[0][1]))
		except:
			pass

		try:	
			total_cash = text_to_num(str(bs.query('`Breakdown`.str.startswith("Total Cash")').iloc[0][1]) + 'k')
		except:
			pass

		try:
			short_term_liabilities = text_to_num(str(bs.query('`Breakdown`.str.startswith("Total Current Liabilities")').iloc[0][1]) + 'k')
		except:
			pass

		try:	
			total_liabilities = text_to_num(str(bs.query('`Breakdown`.str.startswith("Total Liabilities")').iloc[0][1]) + 'k')
		except:
			pass

		try:
			total_assets = text_to_num(str(bs.query('`Breakdown`.str.startswith("Total Assets")').iloc[0][1]) + 'k')
		except:
			pass

		try:
			shares_outstanding = text_to_num(str(st.query('`Attribute`.str.startswith("Shares Outstanding")').iloc[0][1]))
		except:
			pass

		try:
			dividend = text_to_num(str(st.query('`Attribute`.str.startswith("5 Year Average Dividend")').iloc[0][1]))
		except:
			pass

		try:
			has_dividends = text_to_num(str(st.query('`Attribute`.str.startswith("5 Year Average Dividend")').iloc[0][1])) > 0
		except:
			pass
		
		try:
			net_income = text_to_num(str(inc.query('`Breakdown`.str.startswith("Net Income")').iloc[0][2]))
		except:
			pass
	except:
		pass

	# remove or include industries and sectors
	# black_list = ['real estate', 'finance', 'financial', 'gold', 'bank', 'insurance', 'mortgage']
	# white_list = []
	
	white_list = ['utilities', 'renewable', 'groceries', 'consumer', 'defensive']
	black_list = []

	industry_and_sector = ''
	if 'sector' in profile:
		industry_and_sector = profile['sector']

	if 'industry' in profile:
		industry_and_sector += profile['industry']

	if black_list:	
		if any(re.search(desc, industry_and_sector, re.IGNORECASE) for desc in black_list):
			result['blacklisted'] +=1
			reject = True

	if white_list:
		if not any(re.search(desc, industry_and_sector, re.IGNORECASE) for desc in white_list):
			result['blacklisted'] +=1
			reject = True

	# company is solvent
	value = (total_assets - total_liabilities) / shares_outstanding
	if float(value) < float(price):
		result['insolvent'] +=1
		reject = True

	# company not too big or too small
	if float(market_cap) <= 100*1000*1000:
		result['too_small'] += 1
		reject = True

	if float(market_cap) >= 20*1000*1000*1000:
		result['too_big'] +=1
		reject = True

	# must pay any dividend
	if not has_dividends:
		result['no_dividends'] +=1
		reject = True
	
	# must be profitable
	if float(net_income) <= 0:
		result['no_income'] +=1
		reject = True

	# must have 6 months of cash reserves
	if float(short_term_liabilities) == 0 or float(total_cash)/float(short_term_liabilities) <= 0.25:
		result['no_cash'] +=1
		reject = True

	if reject:
		continue
	
	profile['ticker'] = share
	profile['dividend'] = '%.2f%%' % float(dividend)
	profile['value/price'] = '%.4f' % (float(value)/float(price))
	profile['cash/debt'] = '%.4f' % (float(total_cash)/float(short_term_liabilities))
	print (json.dumps(profile, indent=2))
	result['passed'] += 1
	
result['blacklisted'] = '%.2f%%' % float(result['blacklisted']/len(shares)*100)
result['insolvent'] = '%.2f%%' % float(result['insolvent']/len(shares)*100)
result['too_small'] = '%.2f%%' % float(result['too_small']/len(shares)*100)
result['too_big'] = '%.2f%%' % float(result['too_big']/len(shares)*100)
result['no_dividends'] = '%.2f%%' % float(result['no_dividends']/len(shares)*100)
result['no_income'] = '%.2f%%' % float(result['no_income']/len(shares)*100)
result['no_cash'] = '%.2f%%' % float(result['no_cash']/len(shares)*100)

print ("Results: " + json.dumps(result, indent=2))
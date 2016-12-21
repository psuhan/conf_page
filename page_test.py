
import conf_py
import logging
import sys, os
from lxml import etree
import time

#logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

def test1():
	p = conf_py.conf_rest_api()
	p.set_server('http://collab.lge.com/main/rest/api/content')
	page = p.get_page('test_page', 'SICIPT')
	# find table
	for table in page.tree.iter('table'):
		print table

def test2():
	p = conf_py.conf_rest_api()
	p.set_server('http://confluence.augkorea.org/rest/api/content')
	page = p.get_page('playground', 'PG')
	# find table
	if page:
		tables = []
		for t in page.tree.iter('table'):
			tables.append(t)
		# find tbody
		for t in tables[0].iter('tbody'):
			pass
		tr = etree.SubElement(t, 'tr')
		td1 = etree.SubElement(tr, 'td').text = 'row added'
		td2 = etree.SubElement(tr, 'td').text = 'automatically'
		td3 = etree.SubElement(tr, 'td').text = time.asctime()
		#etree.dump(page.tree)
		p.update_page('playground', 'PG', page.get_string())

if os.environ['HOST'] == 'Kayoung-2.local':	## home
	test2()
else:		## office
	test1()

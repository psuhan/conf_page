
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
	page.add_table_row(0, ['row added', 'automatically', time.asctime()])
	p.update_page('playground', 'PG', page.get_string())

if os.environ['HOST'] == 'Kayoung-2.local':	## home
	test2()
else:		## office
	test1()


import conf_py
import logging
import sys

#logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

p = conf_py.conf_rest_api()
p.set_server('http://collab.lge.com/main/rest/api/content')
page = p.get_page('test_page', 'SICIPT')
# find table
for table in page.tree.iter('table'):
	print table

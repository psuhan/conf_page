# -*- coding: utf-8 -*-

from lxml import etree
from lxml.builder import ElementMaker
import requests
import requests_toolbelt
import pickle
import os, sys
import getpass
import json
import logging
import base64

class conf_page(object):
	##{{{
	"""
	Storage format container
	"""
	__ROOT_TAG_HEAD__ = '<root xmlns:ac="confluence_macro">'
	__ROOT_TAG_TAIL__ = '</root>'

	def __init__(self):
		self.title = ''
		self.space = ''
		self.version = 1
		self.page_id = 0
		self.tree = None
		#self.macro1 = ElementMaker(namespace = 'confluence_macro').macro1
		#self.macro2 = ElementMaker(namespace = 'confluence_macro').macro2
		#self.macro3 = ElementMaker(namespace = 'confluence_macro').macro3

	def define_dummy_ns(self, content):
		return self.__ROOT_TAG_HEAD__ + content + self.__ROOT_TAG_TAIL__

	def remove_root_tag(self, content):
		return content[content.find(self.__ROOT_TAG_HEAD__) + len(self.__ROOT_TAG_HEAD__):content.find(self.__ROOT_TAG_TAIL__)]

	def import_string(self, string):
		self.tree = etree.fromstring(self.define_dummy_ns(string))

	def get_string(self):
		ret = ''
		for child in self.tree:
			ret = ret + etree.tostring(child)		
		#return etree.tostring(self.tree)
		return ret
	##}}}

	def add_table_row(self, table, row_data, row=1, head_row=False):
		""" add new row to exsiting table """
		table_list = []
		for t in self.tree.iter('table'):
			table_list.append(t)
		if len(table_list) > table:
			tbody = table_list[table].xpath('tbody')[0]
			tr = etree.Element('tr')
			tbody.insert(row, tr)
			for text in row_data:
				if head_row:
					etree.SubElement(tr, 'th').text = str(text)
				else:
					etree.SubElement(tr, 'td').text = str(text)

class conf_rest_api(object):
	##{{{
	"""
	Access conflucence using REST api
	"""
	__PREVIOUS_SESSION_FOLDER__ = '.python_conf_page_previous_sessions'
	
	def __init__(self):
		#self.headers = {'Content-Type': 'application/json'}
		self.logged = False
		self.server = ''
		self.session=requests.session()
		if os.name == 'nt': ## windows
			self.__PREVIOUS_SESSION_FOLDER__ = os.environ['HOMEDRIVE'] + os.environ['HOMEPATH'] + '\\' + self.__PREVIOUS_SESSION_FOLDER__
		elif os.name == 'posix':  ## linux
			self.__PREVIOUS_SESSION_FOLDER__ = os.environ['HOME'] + '/' + self.__PREVIOUS_SESSION_FOLDER__
		self.last_response_json = {}
		#self.initialize()

	#def initialize(self):
	#	self.title = ''
	#	self.space = ''
	#	self.page_string = ''
	#	self.page_version = 0
	#	self.page_id = 0
	#	#self.page_tree = None

	def __del__(self):
		self.save_sessions()

	def site_file_name(self):
		if os.name == 'nt':
			return self.__PREVIOUS_SESSION_FOLDER__ + '\\{}'.format(base64.b64encode(self.server))
		if os.name == 'posix':
			return self.__PREVIOUS_SESSION_FOLDER__ + '/{}'.format(base64.b64encode(self.server))
	
	def save_sessions(self):
		if self.logged:
			if os.path.isdir(self.__PREVIOUS_SESSION_FOLDER__):
				logging.debug('dir: {} exists.'.format(self.__PREVIOUS_SESSION_FOLDER__))
			else:
				os.system('mkdir {}'.format(self.__PREVIOUS_SESSION_FOLDER__))
				logging.debug('dir: {} created.'.format(self.__PREVIOUS_SESSION_FOLDER__))
				if not os.path.isdir(self.__PREVIOUS_SESSION_FOLDER__):
					print 'cannot create session data folder: {}'.format(self.__PREVIOUS_SESSION_FOLDER__)
					return False
			site_file_name = self.site_file_name()
			with open(site_file_name, 'w') as f:
				cookies = self.session.cookies.get_dict()
				session_data = {'user_id':self.user_id, 'cookies':cookies}
				pickle.dump(session_data, f)
				logging.debug('session data saved to {}'.format(site_file_name))

	def set_server(self, server):
		self.server = server

	def do_login(self):
		if not self.logged and not self.server == '':
			print 'trying to continue previous session'
		else:
			logging.debug('alread logged in or server is not specified')
			return False
		site_file_name = self.site_file_name()
		if os.path.isfile(site_file_name):
			with open(site_file_name, 'r') as f:
				session_data = pickle.load(f)
			self.session.cookies.update(session_data['cookies'])
			self.user_id = session_data['user_id']
			ret = self.session.head(self.server + '?')
			if ret.status_code == 200 and 'X-AUSERNAME' in ret.headers and ret.headers['X-AUSERNAME'] == self.user_id:
				print 'continuing previous session'
				self.logged = True
				logging.debug(ret.status_code)
				logging.debug(ret.headers)
				return True
			else:
				print 'login failed'
				logging.debug('deleting session data')
				os.system('rm {}'.format(site_file_name))
				return False	
		else:
			print 'no saved sessions for {}'.format(self.server)
			self.user_id = raw_input('Confluence user ID: ')
			#ret = self.session.head(self.server + '?', auth=(self.user_id, getpass.getpass('password: ')))
			ret = self.session.get(self.server + '?', auth=(self.user_id, getpass.getpass('password: ')))
			if ret.status_code == 200 and 'X-AUSERNAME' in ret.headers and ret.headers['X-AUSERNAME'] == self.user_id:
				print 'logged in'
				self.logged = True
				return True
			else:
				logging.debug(ret.status_code)
				logging.debug(ret.headers)
				logging.debug(ret.text)
				print 'login failed'
				return False

	def rest_get(self, url, args):
		if self.logged or self.do_login():
			exts = []
			for (key, val) in args.items():
				if type(val) == list:
					exts.append(key + '=' + ','.join(map(str, val)))
				else:
					exts.append(key + '=' + str(val))
			exts = '?' + '&'.join(exts)
			logging.debug('extension: ' + exts)
			ret = self.session.get(self.server + exts)
			if ret.status_code == 200:
				self.last_response_json = json.loads(ret.text)
				return True
			else:
				print 'HTTP respond: {}'.format(ret.status_code)
				return False
		else:
			return False
			
	def get_page_id(self, title, space):
		if self.rest_get(self.server, {'title':title, 'spaceKey':space}):
			if self.last_response_json['size'] < 1:
				print 'no page found titled: {} in space: {}'.format(title, space)
				return None
			elif self.last_response_json['size'] > 1:
				print 'more than 2 pages returned'
				return None
			else:
				return self.last_response_json['results'][0]['id']

	def get_page_version(self, title, space):
		if self.rest_get(self.server, {'title':title, 'spaceKey':space, 'expand':'version'}):
			if self.last_response_json['size'] < 1:
				print 'no page found titled: {} in space: {}'.format(title, space)
				return False
			elif self.last_response_json['size'] > 1:
				print 'more than 2 pages returned'
				return False
			else:
				return self.last_response_json['results'][0]['version']['number']

	def get_page(self, title, space):
		if self.rest_get(self.server, {'title':title, 'spaceKey':space, 'expand':['body.storage', 'version']}):
			if self.last_response_json['size'] < 1:
				print 'no page found titled: {} in space: {}'.format(title, space)
				return False
			elif self.last_response_json['size'] > 1:
				print 'more than 2 pages returned'
				return False
			else:
				page = conf_page()
				page.title = title
				page.space = space
				page.version = self.last_response_json['results'][0]['version']['number']
				page.page_id = self.last_response_json['results'][0]['id']
				page.import_string(self.last_response_json['results'][0]['body']['storage']['value'])
				print 'page downloaded'
				return page
		else:
			print 'cannot get respond from server'
			return False

	def delete_page(self, title, space):
		if self.logged or self.do_login():
			pid = self.get_page_id(title, space)
			if not pid == False:
				ret = self.session.delete(self.server + '/{}'.format(pid))
				if ret.status_code == 204:
					print 'page deleted'
					return True
				else:
					print 'cannot delete page'
			else:
				return False
	
	def upload_page(self, title, space, parent, page_string = ''):
		pid = self.get_page_id(parent, space)
		if pid == False:
			print 'parent page: {} does not exist'.format(parent)
			return False
		else:
			#self.page_string = self.remove_root_tag(ET.tostring(self.page_tree))
			if page_string == '': page_string = self.page_string
			data = {'title':		title,
				'space':		{'key': space},
				'ancestors':	[{'id':pid}],
				'type':			'page',
				'body':			{'storage':{'value': page_string, 'representation':'storage'}}
			}
			res = self.session.post(self.server, json=data)
			if res.status_code == 200:
				print 'page uploaded'
				return True
			else:
				print 'HTTP status code: {}'.format(res.status_code)
				print 'page upload failed'
				return False

	def update_page(self, title, space, page_string = ''):
		pid = self.get_page_id(title, space)
		if pid == False:
			print 'parent page: {} does not exist'.format(parent)
			return False
		ver = self.get_page_version(title, space)
		if ver == False:
			print 'cannot get page version'
			return False
		else:
			if page_string == '': page_string = self.page_string
			ver = ver + 1
			data = {'title':		title,
				'type':			'page',
				'body':			{'storage':{'value': page_string, 'representation':'storage'}},
				'version':		{'number': ver}
			}
			res = self.session.put(self.server + '/{}'.format(pid), json=data)
			if res.status_code == 200:
				print 'page updated'
				return True
			else:
				print 'HTTP status code: {}'.format(res.status_code)
				print 'page update failed'
				return False
		
	def attach_file(self, title, space, file, comment=''):
		""" attach file to an existing collab page """
		pid = self.get_page_id(title, space)
		base_name = os.path.basename(file)
		if pid == False:
			print 'page: {} does not exist'.format(parent)
			return False
		else:
			### see if attachment alread exists
			url = self.server + '/{}/child/attachment?'.format(pid)
			res = self.session.get(url)
			attachments = res.json()['results']
			att_id = None
			for at in attachments:
				if unicode(at['title']) == unicode(base_name):
					att_id = at['id']
			if att_id == None: ## new file
				files = [('file', (base_name, open(file, 'rb'), 'application/octet-stream'))]
				url = self.server + '/{}/child/attachment'.format(pid)
			else:	## update
				files = [('file', (base_name, open(file, 'rb'), 'application/octet-stream')), ('minorEdit', 'true')]
				url = self.server + '/{}/child/attachment/{}/data'.format(pid, att_id)
				print 'file already exist, trying to updates'
			if not comment == '':
				files.append(('comment', comment))
			headers = {'X-Atlassian-Token': 'nocheck'}
			res = self.session.post(url, headers=headers, files=files)
			if res.status_code == 200:
				print 'file attached'
				return True
			else:
				print 'cannot attach/update file'
				#print dump.dump_all(res).decode('utf-8')
				return False
	##}}}

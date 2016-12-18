# -*- coding: utf-8 -*-

import lxml.etree as ET
import requests
import requests_toolbelt
import pickle
import os, sys
import getpass
import json
import logging

class page(object):
	"""
	create, modify and upload pages to Atlassian Confluence
	"""

	__ROOT_TAG_HEAD__ = '<root xmlns:ac="confluence_macro">'
	__ROOT_TAG_TAIL__ = '</root>'
	__PREVIOUS_SESSION_DATA__ = '.previous_session_data'

	def __init__(self):
		#self.headers = {'Content-Type': 'application/json'}
		self.__logged = False
		self.rest_server = ''
		self.session=requests.session()
		self.__PREVIOUS_SESSION_DATA__ = os.environ['HOME'] + '/' + self.__PREVIOUS_SESSION_DATA__
		self.last_response_json = {}
		self.initialize()

	def initialize(self):
		self.title = ''
		self.space = ''
		self.synced = False
		self.page_string = ''
		self.page_version = 0
		self.page_id = 0
		self.page_tree = None

	def __del__(self):
		self.save_session_id()

	def save_session_id(self):
		if self.__logged:
			with open(self.__PREVIOUS_SESSION_DATA__, 'w') as f:
				cookies = self.session.cookies.get_dict()
				session_data = {'JSESSIONID':cookies['JSESSIONID'], 'user_id':self.user_id}
				pickle.dump(session_data, f)
			print 'session data saved to {}'.format(self.__PREVIOUS_SESSION_DATA__)

	def set_rest_server(self, server):
		self.rest_server = server

	def __define_dummy_ns(self, content):
		return self.__ROOT_TAG_HEAD__ + content + self.__ROOT_TAG_TAIL__

	def __remove_root_tag(self, content):
		return content[content.find(self.__ROOT_TAG_HEAD__) + len(self.__ROOT_TAG_HEAD__):content.find(self.__ROOT_TAG_TAIL__)]

	def do_login(self):
		if os.path.isfile(self.__PREVIOUS_SESSION_DATA__):
			print 'trying to continue previous session'
			with open(self.__PREVIOUS_SESSION_DATA__, 'r') as f:
				session_data = pickle.load(f)
			self.session.cookies.update({'JSESSIONID':session_data['JSESSIONID']})
			ret = self.session.head(self.rest_server + '?')
			if ret.status_code == 200 and ret.headers['X-AUSERNAME'] == session_data['user_id']:
				print 'continuing previous session'
				self.__logged = True
				self.user_id = session_data['user_id']
				return True
			else:
				print 'login failed'
				return False
		else:
			self.user_id = raw_input('Confluence user ID: ')
			ret = self.session.head(self.rest_server + '?', auth=(self.user_id, getpass.getpass('password: ')))
			if ret.status_code == 200 and ret.headers['X-AUSERNAME'] == self.user_id:
				print 'logged in'
				self.__logged = True
				return True
			else:
				print 'login failed'
				return False

	def rest_api_get(self, url, args):
		if self.__logged or self.do_login():
			exts = []
			for (key, val) in args.items():
				if type(val) == list:
					exts.append(key + '=' + ','.join(map(str, val)))
				else:
					exts.append(key + '=' + str(val))
			exts = '?' + '&'.join(exts)
			logging.debug('extension: ' + exts)
			ret = self.session.get(self.rest_server + exts)
			if ret.status_code == 200:
				self.last_response_json = json.loads(ret.text)
				return True
			else:
				print 'HTTP respond: {}'.format(ret.status_code)
				return False
		else:
			print 'failed to login'
			return False
			
	def get_page_from_server(self, title, space):
		if self.rest_api_get(self.rest_server, {'title':title, 'spaceKey':space, 'expand':['body.storage', 'version']}):
			if self.last_response_json['size'] < 1:
				print 'no page found titled: {} in space: {}'.format(title, space)
				return False
			elif self.last_response_json['size'] > 1:
				print 'more than 2 pages returned'
				return False
			else:
				self.page_string = self.last_response_json['results'][0]['body']['storage']['value']
				self.version = self.last_response_json['results'][0]['version']['number']
				self.page_id = self.last_response_json['results'][0]['id']
				self.page_tree = ET.fromstring(self.__define_dummy_ns(self.page_string))
				self.title = title
				self.space = space
				self.synced = True
				return True
		else:
			print 'cannot get respond from server'
			return False

	def create_new_page_offline(self):
		self.initialize()
		self.synced = False
		self.page_tree = ET.fromstring(self.__ROOT_TAG_HEAD__ + self.__ROOT_TAG_TAIL__)

	def get_page_id_from_title(self, title, space):
		if self.rest_api_get(self.rest_server, {'title':title, 'spaceKey':space}):
			if self.last_response_json['size'] < 1:
				print 'no page found titled: {} in space: {}'.format(title, space)
				return False
			elif self.last_response_json['size'] > 1:
				print 'more than 2 pages returned'
				return False
			else:
				return self.last_response_json['results'][0]['id']

	def delete_page(self, title, space):
		if self.__logged or self.do_login():
			pid = self.get_page_id_from_title(title, space)
			if not pid == False:
				ret = self.session.delete(self.rest_server + '/{}'.format(pid))
				if ret.status_code == 204:
					print 'page deleted'
					return True
				else:
					print 'cannot delete page'
			else:
				#print 'no page found titled: {} in space: {}'.format(title, space)
				return False
	
	def upload_page_to_web(self, title, space, parent):
		if self.synced:
			print 'page already synced to web'
			return False
		else:
			pid = self.get_page_id_from_title(parent, space)
			if pid == None:
				print 'parent page: {} does not exist'.format(parent)
			else:
				self.page_string = self.__remove_root_tag(ET.tostring(self.page_tree))
				#print self.page_string
				data = {'title':		title,
				        'space':		{'key': space},
				        'ancestors':	[{'id':pid}],
				        'type':			'page',
				        'body':			{'storage':{'value': self.page_string, 'representation':'storage'}}
				}
				res = self.session.post(self.rest_server, json=data)
				if res.status_code == 200:
					self.synced = True
					self.title = title
					self.space = space
					#Self.page_version = 0
					#Self.page_id = 0
				else:
					print 'HTTP status code: {}'.format(res.status_code)
					print 'page upload failed'

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
#p = page()
#p.set_rest_server('http://collab.lge.com/main/rest/api/content')
#p.get_page_from_server('test_document', 'SICIPT')
#print p.version
#print p.page_string
#print p.get_page_id_from_title('test_document', 'SICIPT')
p2 = page()
p2.set_rest_server('http://confluence.augkorea.org/rest/api/content')
p2.delete_page('child1', 'PG')
p2.delete_page('child2', 'PG')
#p2.delete_page('test_document5', 'PG')
#p2.delete_page('test_document6', 'PG')
#p2.get_page_from_server('playground', 'PG')
#p2.create_new_page_offline()
#p = ET.SubElement(p2.page_tree, 'p')
#p.text = 'new page'
#p2.upload_page_to_web('test_document6', 'PG', 'playground')




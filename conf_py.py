# -*- coding: utf-8 -*-

import lxml.etree as ET
import requests
import requests_toolbelt
import pickle
import os, sys
import getpass
import json
import logging
import base64

class page(object):
	"""
	create, modify and upload pages to Atlassian Confluence
	itended to run on Linux
	"""

	__ROOT_TAG_HEAD__ = '<root xmlns:ac="confluence_macro">'
	__ROOT_TAG_TAIL__ = '</root>'
	__PREVIOUS_SESSION_FOLDER__ = '.python_conf_page_previous_sessions'

	def __init__(self):
		#self.headers = {'Content-Type': 'application/json'}
		self.logged = False
		self.rest_server = ''
		self.session=requests.session()
		self.__PREVIOUS_SESSION_FOLDER__ = os.environ['HOME'] + '/' + self.__PREVIOUS_SESSION_FOLDER__
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
		self.save_sessions()

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
			site_file_name = self.__PREVIOUS_SESSION_FOLDER__ + '/{}'.format(base64.b64encode(self.rest_server))
			with open(site_file_name, 'w') as f:
				cookies = self.session.cookies.get_dict()
				session_data = {'user_id':self.user_id, 'cookies':cookies}
				pickle.dump(session_data, f)
				logging.debug('session data saved to {}'.format(site_file_name))

	def set_rest_server(self, server):
		self.rest_server = server

	def define_dummy_ns(self, content):
		return self.__ROOT_TAG_HEAD__ + content + self.__ROOT_TAG_TAIL__

	def remove_root_tag(self, content):
		return content[content.find(self.__ROOT_TAG_HEAD__) + len(self.__ROOT_TAG_HEAD__):content.find(self.__ROOT_TAG_TAIL__)]

	def do_login(self):
		if not self.logged and not self.rest_server == '':
			print 'trying to continue previous session'
		else:
			logging.debug('alread logged in or server is not specified')
			return False
		site_file_name = self.__PREVIOUS_SESSION_FOLDER__ + '/{}'.format(base64.b64encode(self.rest_server))
		if os.path.isfile(site_file_name):
			with open(site_file_name, 'r') as f:
				session_data = pickle.load(f)
			self.session.cookies.update(session_data['cookies'])
			self.user_id = session_data['user_id']
			ret = self.session.head(self.rest_server + '?')
			#if ret.status_code == 200 and ret.headers['X-AUSERNAME'] == self.user_id:
			if ret.status_code == 200 and 'X-AUSERNAME' in ret.headers and ret.headers['X-AUSERNAME'] == self.user_id:
				print 'continuing previous session'
				self.logged = True
				return True
			else:
				print 'login failed'
				return False
		else:
			print 'no saved sessions for {}'.format(self.rest_server)
			self.user_id = raw_input('Confluence user ID: ')
			ret = self.session.head(self.rest_server + '?', auth=(self.user_id, getpass.getpass('password: ')))
			#if ret.status_code == 200 and ret.headers['X-AUSERNAME'] == self.user_id:
			if ret.status_code == 200 and 'X-AUSERNAME' in ret.headers and ret.headers['X-AUSERNAME'] == self.user_id:
				print 'logged in'
				self.logged = True
				return True
			else:
				print ret.headers
				print ret.text
				print 'login failed'
				return False

	def rest_api_get(self, url, args):
		if self.logged or self.do_login():
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
				self.page_tree = ET.fromstring(self.define_dummy_ns(self.page_string))
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
		if self.logged or self.do_login():
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
				self.page_string = self.remove_root_tag(ET.tostring(self.page_tree))
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


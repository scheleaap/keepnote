# -*- coding: utf-8 -*-

import base64
import os
import unittest

from keepnote.notebooknew import *
from keepnote.notebooknew.storage import NotebookStorage, StoredNode
from keepnote.notebooknew.storage.mem import InMemoryStorage
from test.notebooknew.storage import DEFAULT_HTML_PAYLOAD_NAME

DEFAULT_ID = 'my_id'
DEFAULT_CONTENT_TYPE = CONTENT_TYPE_HTML
DEFAULT_TITLE = 'my_title'
DEFAULT_PAYLOAD_NAMES = ['my_payload1', 'my_payload2']
DEFAULT_HTML_PAYLOAD_NAME = os.path.basename('index.html')
DEFAULT_HTML_PAYLOAD = base64.b64decode('PCFET0NUWVBFIGh0bWw+DQoNCjxoMT5UZXN0IE5vZGU8L2gxPg0KPHA+VGhpcyBpcyBhIG5vZGUgdXNlZCBmb3IgdGVzdGluZy48L3A+DQo=')
DEFAULT_PNG_PAYLOAD_NAME = os.path.basename('image.png')
DEFAULT_PNG_PAYLOAD = base64.b64decode('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')


class ContentNodeTest(unittest.TestCase, ContentFolderNodeTestBase):
	def test_equals(self):
		def create_node(
				self,
				node_id=DEFAULT_ID,
				content_type=DEFAULT_CONTENT_TYPE,
				is_dirty=True,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				new_payloads='default',
				parent=None,
				payload_names='default',
				title=DEFAULT_TITLE,
				):
			
			if new_payloads == 'default':
				new_payloads = [(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD)]
			if payload_names == 'default':
				payload_names = DEFAULT_PAYLOAD_NAMES
			
			return ContentNode(
					node_id=node_id,
					content_type=content_type,
					is_dirty=is_dirty,
					main_payload_name=main_payload_name,
					new_payloads=new_payloads,
					parent=parent,
					payload_names=payload_names,
					title=title,
					)
		
		#TODO: OOK ALLE ATTRIBUTEN VAN NOTEBOOKNODE TESTEN
		parent = self._create_node()
		
		node1 = self._create_node(parent=parent)
		node1a = self._create_node(parent=parent)

		self.assertTrue(node1 == node1a)
		self.assertFalse(node1 != node1a)

		node2 = self._create_node(parent=parent, main_payload_name=None)
		node3 = self._create_node(parent=parent, new_payloads=None)
		node4 = self._create_node(parent=parent, payload_names=None)

		self.assertFalse(node1 == node2)
		self.assertFalse(node1 == node3)
		self.assertFalse(node1 == node4)
		self.assertTrue(node1 != node2)
		self.assertTrue(node1 != node3)
		self.assertTrue(node1 != node4)

		self.assertFalse(node1 == 'asdf')
	

class FolderNodeTest(unittest.TestCase, ContentAndFolderNodeTestBase):
	def test_equals(self):
		def create_node(
				self,
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_FOLDER,
				is_dirty=True,
				parent=None,
				title=DEFAULT_TITLE,
				):
			
			return FolderNode(
					node_id=node_id,
					content_type=content_type,
					is_dirty=is_dirty,
					parent=parent,
					title=title,
					)
		
		#TODO: OOK ALLE ATTRIBUTEN VAN NOTEBOOKNODE TESTEN
		parent = self._create_node()
		
		node1 = self._create_node(parent=parent)
		node1a = self._create_node(parent=parent)

		self.assertTrue(node1 == node1a)
		self.assertFalse(node1 != node1a)

		node2 = self._create_node(parent=parent, main_payload_name=None)
		node3 = self._create_node(parent=parent, new_payloads=None)
		node4 = self._create_node(parent=parent, payload_names=None)

		self.assertFalse(node1 == node2)
		self.assertFalse(node1 == node3)
		self.assertFalse(node1 == node4)
		self.assertTrue(node1 != node2)
		self.assertTrue(node1 != node3)
		self.assertTrue(node1 != node4)

		self.assertFalse(node1 == 'asdf')

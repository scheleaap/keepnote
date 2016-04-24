# -*- coding: utf-8 -*-

from __future__ import absolute_import
import base64
import copy
from datetime import datetime
from hamcrest import *
import io
import mock
from mock import Mock, call
import os
from pytz import utc
import re
from time import sleep
import unittest

from keepnote.notebooknew import *
from keepnote.notebooknew import CONTENT_TYPE_HTML, CONTENT_TYPE_TRASH, CONTENT_TYPE_FOLDER
from keepnote.notebooknew import new_node_id
import keepnote.notebooknew.storage as storage
from keepnote.notebooknew.storage import StoredNode
import keepnote.notebooknew.storage.mem
from keepnote.pref import Pref

from .testutils import *

MS = 0.001  # 1 millisecond in seconds



def add_stored_node(notebook_storage, sn):
	notebook_storage.add_node(
			node_id=sn.node_id,
			content_type=sn.content_type,
			attributes=sn.attributes,
			payloads=[]
			)

def datetime_to_timestamp(dt):
	# From https://docs.python.org/3.3/library/datetime.html#datetime.datetime.timestamp
	return (dt - datetime(1970, 1, 1, tzinfo=utc)).total_seconds()

class NotebookTest(unittest.TestCase):
	def _create_notebook(self,
			title=DEFAULT_TITLE
			):
		return Notebook(
				title=title,
				)
	
	def setUp(self):
		self._event_handler = Mock()
	
	def test_client_preferences(self):
		"""Test the setting and getting of Notebook client preferences."""
		
		# Initialize Notebook.
		notebook = self._create_notebook()
		
		expected = Pref()
		self.assertEqual(expected, notebook.client_preferences)
		
		notebook.client_preferences.get('test', 'key', define=True)
		notebook.client_preferences.set('test', 'key', 'value')
		
		expected = Pref()
		expected.get('test', 'key', define=True)
		expected.set('test', 'key', 'value')
		self.assertEqual(expected, notebook.client_preferences)
	
	def test_close_without_changes(self):
		notebook = self._create_notebook()
		notebook.closing_listeners.add(self._event_handler.on_closing)
		notebook.close_listeners.add(self._event_handler.on_close)
		
		notebook.close()
		
		self._event_handler.assert_has_calls([call.on_closing(notebook), call.on_close(notebook)])
	
	def test_add_node_added_listener(self):
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = []
		
		notebook = Notebook(notebook_storage)
		notebook.node_added_listeners.add(self._event_handler.on_node_added)
	
	def test_add_node_removed_listener(self):
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = []
		
		notebook = Notebook(notebook_storage)
		notebook.node_removed_listeners.add(self._event_handler.on_node_removed)
	
	def test_add_node_moved_listener(self):
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = []
		
		notebook = Notebook(notebook_storage)
		notebook.node_moved_listeners.add(self._event_handler.on_node_moved)
	
	def test_add_node_changed_listener(self):
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = []
		
		notebook = Notebook(notebook_storage)
		notebook.node_changed_listeners.add(self._event_handler.on_node_changed)
	
	def add_client_event_listener(self):
		notebook = self._create_notebook()
		notebook.get_client_event_listeners("my-event").add(self._event_handler.on_event)
	
	def test_set_root(self):
		notebook = self._create_notebook()
		
		with self.assertRaises(Exception):
			notebook.root = TestNotebookNode()
		
		self.assertEqual(None, notebook.root)
	
	def test_add_new_node_as_root(self):
		notebook = self._create_notebook()
		notebook.node_added_listeners.add(self._event_handler.on_node_added)
		node = TestNotebookNode(notebook=None, parent=None)
		
		assert_that(notebook.can_add_new_node_as_root(), is_(True))
		
		notebook.add_new_node_as_root(node)
		
		assert_that(notebook.root, is_(same_instance(node)))
		assert_that(node._notebook, is_(same_instance(notebook)))
		assert_that(node.parent, is_(none()))
		self._event_handler.assert_has_calls([call.on_node_added(node, parent=None)])
	
	def test_add_new_node_as_root_node_notebook_not_none(self):
		notebook = self._create_notebook()
		notebook.node_added_listeners.add(self._event_handler.on_node_added)
		node = TestNotebookNode(notebook=notebook, parent=None)
		
		with self.assertRaises(Exception):
			notebook.add_new_node_as_root(node)
		
		assert_that(notebook.root, is_(none()))
		assert_that(node._notebook, is_(same_instance(notebook)))
		assert_that(node.parent, is_(none()))
	
	def test_add_new_node_as_root_node_parent_not_none(self):
		notebook = self._create_notebook()
		notebook.node_added_listeners.add(self._event_handler.on_node_added)
		other_parent = TestNotebookNode()
		node = TestNotebookNode(parent=other_parent, add_to_parent=True)
		
		with self.assertRaises(Exception):
			notebook.add_new_node_as_root(node)
		
		assert_that(notebook.root, is_(none()))
		assert_that(node._notebook, is_(none()))
		assert_that(node.parent, is_(same_instance(other_parent)))
	
	def test_add_new_node_as_root_node_deleted(self):
		notebook = self._create_notebook()
		notebook.node_added_listeners.add(self._event_handler.on_node_added)
		node = TestNotebookNode()
		node.delete()
		
		with self.assertRaises(Exception):
			notebook.add_new_node_as_root(node)
		
		assert_that(notebook.root, is_(none()))
		assert_that(node._notebook, is_(none()))
		assert_that(node.parent, is_(none()))
	
	def test_add_new_node_as_root_root_already_present(self):
		notebook = self._create_notebook()
		notebook.node_added_listeners.add(self._event_handler.on_node_added)
		node1 = TestNotebookNode()
		node2 = TestNotebookNode()
		notebook.add_new_node_as_root(node1)
		
		assert_that(notebook.can_add_new_node_as_root(), is_(False))
		
		with self.assertRaises(Exception):
			notebook.add_new_node_as_root(node2)
		
		assert_that(notebook.root, is_(same_instance(node1)))
		assert_that(node1._notebook, is_(same_instance(notebook)))
		assert_that(node2._notebook, is_(none()))
	
	def test_has_node(self):
		root = TestNotebookNode()
		child1 = TestNotebookNode(parent=root, add_to_parent=True)
		child11 = TestNotebookNode(parent=child1, add_to_parent=True)
		child12 = TestNotebookNode(parent=child1, add_to_parent=True)
		child121 = TestNotebookNode(parent=child12, add_to_parent=True)
		notebook = self._create_notebook()
		notebook._root = root

		self.assertEqual(True, notebook.has_node(root.node_id))
		self.assertEqual(True, notebook.has_node(child1.node_id))
		self.assertEqual(True, notebook.has_node(child11.node_id))
		self.assertEqual(True, notebook.has_node(child12.node_id))
		self.assertEqual(True, notebook.has_node(child121.node_id))
		self.assertEqual(False, notebook.has_node('other_id'))
	
	def test_find_node_by_id(self):
		root = TestNotebookNode()
		child1 = TestNotebookNode(parent=root, add_to_parent=True)
		child11 = TestNotebookNode(parent=child1, add_to_parent=True)
		child12 = TestNotebookNode(parent=child1, add_to_parent=True)
		child121 = TestNotebookNode(parent=child12, add_to_parent=True)
		notebook = self._create_notebook()
		notebook._root = root

		self.assertEqual(root, notebook.get_node_by_id(root.node_id))
		self.assertEqual(child1, notebook.get_node_by_id(child1.node_id))
		self.assertEqual(child11, notebook.get_node_by_id(child11.node_id))
		self.assertEqual(child12, notebook.get_node_by_id(child12.node_id))
		self.assertEqual(child121, notebook.get_node_by_id(child121.node_id))
		with self.assertRaises(NodeDoesNotExistError):
			notebook.get_node_by_id('other_id')
	
	def test_title_init_set(self):
		"""Tests setting the title of a notebook."""
		notebook = Notebook(title=DEFAULT_TITLE)
		
		self.assertEqual(DEFAULT_TITLE, notebook.title)

		# Change the notebook's title.
		notebook.title = 'new title'
		
		self.assertEqual('new title', notebook.title)
# 		self.assertEqual(True, notebook.is_dirty)


class ContentFolderTrashNodeTestBase(object):
	def _create_notebook(self):
		return Notebook(title=DEFAULT_TITLE)
	
	def _create_node(
			self,
			notebook=None,
			parent=None,
			loaded_from_storage=False,
			title=DEFAULT_TITLE,
			order=DEFAULT_ORDER,
			icon_normal=DEFAULT_ICON_NORMAL,
			icon_open=DEFAULT_ICON_OPEN,
			title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
			title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
			client_preferences=DEFAULT_CLIENT_PREFERENCES,
			node_id=DEFAULT,
			created_time=DEFAULT,
			modified_time=DEFAULT,
			):
		"""Creates a node of the class under test."""
		raise NotImplementedError()
	
	def setUp(self):
		self._notebook = self._create_notebook()
		self._event_handler = Mock()
		
		# Register event handlers.
		self._notebook.node_added_listeners.add(self._event_handler.on_node_added)
		self._notebook.node_removed_listeners.add(self._event_handler.on_node_removed)
		self._notebook.node_moved_listeners.add(self._event_handler.on_node_moved)
		self._notebook.node_changed_listeners.add(self._event_handler.on_node_changed)
	
	def test_create_new_n(self):
		parent = TestNotebookNode()
		
		node = self._create_node(
				parent=parent,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				order=DEFAULT_ORDER,
				icon_normal=DEFAULT_ICON_NORMAL,
				icon_open=DEFAULT_ICON_OPEN,
				title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
				title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
				client_preferences=DEFAULT_CLIENT_PREFERENCES,
				)
		
		self.assertEqual(AnyUuidMatcher(), node.node_id)
		self.assertEqual(parent, node.parent)
# 		self.assertEqual(DEFAULT_TITLE, node.title)
# 		self.assertEqual(True, abs((datetime.now() - node.created_time).total_seconds()) < 1)
# 		self.assertEqual(node.created_time, node.modified_time)
		self.assertEqual(DEFAULT_ORDER, node.order)
		self.assertEqual(DEFAULT_ICON_NORMAL, node.icon_normal)
		self.assertEqual(DEFAULT_ICON_OPEN, node.icon_open)
		self.assertEqual(DEFAULT_TITLE_COLOR_FOREGROUND, node.title_color_foreground)
		self.assertEqual(DEFAULT_TITLE_COLOR_BACKGROUND, node.title_color_background)
		self.assertEqual(Pref(DEFAULT_CLIENT_PREFERENCES), node.client_preferences)
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(False, node.is_deleted)
		self.assertEqual(False, node.has_children())
		self.assertEqual([], node.children)
		repr(node)
		
	def test_create_from_storage_n(self):
		parent = TestNotebookNode()
		
		node = self._create_node(
				parent=parent,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				order=DEFAULT_ORDER,
				icon_normal=DEFAULT_ICON_NORMAL,
				icon_open=DEFAULT_ICON_OPEN,
				title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
				title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
				client_preferences=DEFAULT_CLIENT_PREFERENCES,
				node_id=DEFAULT_ID,
				created_time=DEFAULT_CREATED_TIME,
				modified_time=DEFAULT_MODIFIED_TIME,
				)
		
		self.assertEqual(DEFAULT_ID, node.node_id)
		self.assertEqual(parent, node.parent)
# 		self.assertEqual(DEFAULT_TITLE, node.title)
# 		self.assertEqual(DEFAULT_CREATED_TIME, node.created_time)
# 		self.assertEqual(DEFAULT_MODIFIED_TIME, node.modified_time)
		self.assertEqual(DEFAULT_ORDER, node.order)
		self.assertEqual(DEFAULT_ICON_NORMAL, node.icon_normal)
		self.assertEqual(DEFAULT_ICON_OPEN, node.icon_open)
		self.assertEqual(DEFAULT_TITLE_COLOR_FOREGROUND, node.title_color_foreground)
		self.assertEqual(DEFAULT_TITLE_COLOR_BACKGROUND, node.title_color_background)
		self.assertEqual(Pref(DEFAULT_CLIENT_PREFERENCES), node.client_preferences)
		self.assertEqual(False, node.is_dirty)
		self.assertEqual(False, node.is_deleted)
		self.assertEqual(False, node.has_children())
		self.assertEqual([], node.children)
		repr(node)
	
	def test_constructor_parameters_new_n1(self):
		with self.assertRaises(IllegalArgumentCombinationError):
			self._create_node(
					loaded_from_storage=False,
					node_id='12345',  # Must be None if not loaded from storage
					)
	
	def test_constructor_parameters_new_n2(self):
		with self.assertRaises(IllegalArgumentCombinationError):
			self._create_node(
					loaded_from_storage=False,
					created_time=datetime.now(),  # Must be None if not loaded from storage
					)
	
	def test_constructor_parameters_new_n3(self):
		with self.assertRaises(IllegalArgumentCombinationError):
			self._create_node(
					loaded_from_storage=False,
					modified_time=datetime.now(),  # Must be None if not loaded from storage
					)
	
	def test_constructor_parameters_from_storage_n1(self):
		with self.assertRaises(IllegalArgumentCombinationError):
			self._create_node(
					loaded_from_storage=True,
					node_id=None,  # Must be not None if loaded from storage
					)
	
	def test_is_root_1(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		
		self.assertEqual(True, node.is_root)
	
	def test_is_root_2(self):
		parent = TestNotebookNode()
		
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		self.assertEqual(False, node.is_root)
	
	def test_is_node_a_child_1(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		child = TestNotebookNode(parent=node, add_to_parent=True)
		
		self.assertEqual(True, node.is_node_a_child(child))
	
	def test_is_node_a_child_2(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		child1 = TestNotebookNode(parent=node, add_to_parent=True)
		child11 = TestNotebookNode(parent=child1, add_to_parent=True)
		
		self.assertEqual(True, node.is_node_a_child(child11))
	
	def test_is_node_a_child_3(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		
		self.assertEqual(False, node.is_node_a_child(node))
	
	def test_is_node_a_child_4(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		other_node = TestNotebookNode(parent=None)
		
		self.assertEqual(False, node.is_node_a_child(other_node))
	
	def test_title_init_set_new(self):
		"""Tests setting the title of a new node."""
		node = self._create_node(notebook=self._notebook, title=DEFAULT_TITLE, loaded_from_storage=False)
		self.assertEqual(DEFAULT_TITLE, node.title)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title.
		node.title = 'new title'
		
		self.assertEqual('new title', node.title)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self._event_handler.assert_has_calls([call.on_node_changed(node)])

	def test_title_init_set_from_storage(self):
		"""Tests setting the title of a node loaded from storage."""
		node = self._create_node(notebook=self._notebook, title=DEFAULT_TITLE, loaded_from_storage=True)
		self.assertEqual(DEFAULT_TITLE, node.title)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title.
		node.title = 'new title'
		
		self.assertEqual('new title', node.title)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self._event_handler.assert_has_calls([call.on_node_changed(node)])
	
	def test_title_create_copy(self):
		node = self._create_node(title=DEFAULT_TITLE, loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.title, equal_to(node.title))
	
	def test_created_time_init_new(self):
		"""Tests the created time of a new node."""
		node = self._create_node(loaded_from_storage=False)
		self.assertEqual(utc, node.created_time.tzinfo)
		self.assertEqual(True, abs(utc.localize(datetime.utcnow()) - node.created_time).total_seconds() < 5)
		original_created_time = node.created_time

		# Try changing the node's created time.
		with self.assertRaises(Exception):
			node.created_time = datetime.now(tz=utc)
		
		self.assertEqual(original_created_time, node.created_time)
# 		self.assertEqual(True, node.is_dirty)
	
	def test_created_time_init_from_storage(self):
		"""Tests the created time of a node loaded from storage."""
		node = self._create_node(created_time=DEFAULT_CREATED_TIME, loaded_from_storage=True)
		self.assertEqual(utc, node.created_time.tzinfo)
		self.assertEqual(DEFAULT_CREATED_TIME, node.created_time)
		original_created_time = node.created_time

		# Try changing the node's created time.
		with self.assertRaises(Exception):
			node.created_time = datetime.now(tz=utc)

# 		self.assertEqual(False, node.is_dirty)
		self.assertEqual(original_created_time, node.created_time)
	
	def test_created_time_init_unset(self):
		"""Tests loading a node from storage without a created time."""
		node = self._create_node(created_time=None, loaded_from_storage=True)
		self.assertEqual(None, node.created_time)
	
	def test_created_time_create_copy(self):
		node = self._create_node(loaded_from_storage=False)
		sleep(1 * MS)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.created_time.tzinfo, is_(same_instance(utc)))
		assert_that(abs(utc.localize(datetime.utcnow()) - copy.created_time).total_seconds(), is_(less_than(1)))
		assert_that(copy.created_time, is_not(equal_to(node.created_time)))
	
	def test_modified_time_init_new(self):
		"""Tests saving the modified time of a new node."""
		node = self._create_node(loaded_from_storage=False)
		self.assertEqual(utc, node.modified_time.tzinfo)
		self.assertEqual(node.created_time, node.modified_time)

		# Change the node's modified time.
		new_modified_time = datetime.now(tz=utc)
		node.modified_time = new_modified_time
		
		self.assertEqual(new_modified_time, node.modified_time)
# 		self.assertEqual(True, node.is_dirty)
	
	def test_modified_time_init_from_storage(self):
		"""Tests saving the modified time of a node loaded from storage."""
		node = self._create_node(modified_time=DEFAULT_MODIFIED_TIME, loaded_from_storage=True)
		self.assertEqual(utc, node.modified_time.tzinfo)
		self.assertEqual(DEFAULT_MODIFIED_TIME, node.modified_time)

		# Change the node's modified time.
		new_modified_time = datetime.now(tz=utc)
		node.modified_time = new_modified_time
		
		self.assertEqual(new_modified_time, node.modified_time)
# 		self.assertEqual(True, node.is_dirty)
	
	def test_modified_time_create_copy(self):
		node = self._create_node(loaded_from_storage=False)
		sleep(1 * MS)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.created_time.tzinfo, is_(same_instance(utc)))
		assert_that(copy.modified_time, equal_to(copy.created_time))
	
	def test_icon_normal_init_set_new(self):
		"""Tests setting the normal icon of a new node."""
		node = self._create_node(notebook=self._notebook, icon_normal=DEFAULT_ICON_NORMAL, loaded_from_storage=False)
		self.assertEqual(DEFAULT_ICON_NORMAL, node.icon_normal)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's normal icon.
		node.icon_normal = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.icon_normal)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self._event_handler.assert_has_calls([call.on_node_changed(node)])
	
	def test_icon_normal_init_set_from_storage(self):
		"""Tests setting the normal icon of a node loaded from storage."""
		node = self._create_node(notebook=self._notebook, icon_normal=DEFAULT_ICON_NORMAL, loaded_from_storage=True)
		self.assertEqual(DEFAULT_ICON_NORMAL, node.icon_normal)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's normal icon.
		node.icon_normal = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.icon_normal)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self._event_handler.assert_has_calls([call.on_node_changed(node)])
	
	def test_icon_normal_create_copy(self):
		node = self._create_node(icon_normal=DEFAULT_ICON_NORMAL, loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.icon_normal, equal_to(node.icon_normal))
	
	def test_icon_open_init_set_new(self):
		"""Tests setting the open icon of a new node."""
		node = self._create_node(notebook=self._notebook, icon_open=DEFAULT_ICON_OPEN, loaded_from_storage=False)
		self.assertEqual(DEFAULT_ICON_OPEN, node.icon_open)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's open icon.
		node.icon_open = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.icon_open)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self._event_handler.assert_has_calls([call.on_node_changed(node)])
	
	def test_icon_open_init_set_from_storage(self):
		"""Tests setting the open icon of a node loaded from storage."""
		node = self._create_node(notebook=self._notebook, icon_open=DEFAULT_ICON_OPEN, loaded_from_storage=True)
		self.assertEqual(DEFAULT_ICON_OPEN, node.icon_open)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's open icon.
		node.icon_open = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.icon_open)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self._event_handler.assert_has_calls([call.on_node_changed(node)])
	
	def test_icon_open_create_copy(self):
		node = self._create_node(icon_open=DEFAULT_ICON_OPEN, loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.icon_open, equal_to(node.icon_open))
	
	def test_title_color_foreground_init_set_new(self):
		"""Tests setting the title foreground color of a new node."""
		node = self._create_node(notebook=self._notebook, title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND, loaded_from_storage=False)
		self.assertEqual(DEFAULT_TITLE_COLOR_FOREGROUND, node.title_color_foreground)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title foreground color.
		node.title_color_foreground = '#c0c0c0'
		
		self.assertEqual('#c0c0c0', node.title_color_foreground)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self._event_handler.assert_has_calls([call.on_node_changed(node)])
	
	def test_title_color_foreground_init_set_from_storage(self):
		"""Tests setting the title foreground of a node loaded from storage."""
		node = self._create_node(notebook=self._notebook, title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND, loaded_from_storage=True)
		self.assertEqual(DEFAULT_TITLE_COLOR_FOREGROUND, node.title_color_foreground)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title foreground color.
		node.title_color_foreground = '#c0c0c0'
		
		self.assertEqual('#c0c0c0', node.title_color_foreground)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self._event_handler.assert_has_calls([call.on_node_changed(node)])
	
	def test_title_color_foreground_create_copy(self):
		node = self._create_node(title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND, loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.title_color_foreground, equal_to(node.title_color_foreground))
	
	def test_title_color_background_init_set_new(self):
		"""Tests setting the title background color of a new node."""
		node = self._create_node(notebook=self._notebook, title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND, loaded_from_storage=False)
		self.assertEqual(DEFAULT_TITLE_COLOR_BACKGROUND, node.title_color_background)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title background color.
		node.title_color_background = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.title_color_background)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self._event_handler.assert_has_calls([call.on_node_changed(node)])
	
	def test_title_color_background_init_set_from_storage(self):
		"""Tests setting the title background color of a node loaded from storage."""
		node = self._create_node(notebook=self._notebook, title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND, loaded_from_storage=True)
		self.assertEqual(DEFAULT_TITLE_COLOR_BACKGROUND, node.title_color_background)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title background color.
		node.title_color_background = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.title_color_background)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self._event_handler.assert_has_calls([call.on_node_changed(node)])
	
	def test_title_color_background_create_copy(self):
		node = self._create_node(title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND, loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.title_color_background, equal_to(node.title_color_background))
	
	def test_client_preferences_init_set_new(self):
		"""Tests setting the client preferences of a new node."""
		node = self._create_node(notebook=self._notebook, client_preferences=DEFAULT_CLIENT_PREFERENCES, loaded_from_storage=False)
		self.assertEqual(DEFAULT_CLIENT_PREFERENCES, node.client_preferences._data)
		old_modified_time = node.modified_time
		sleep(1 * MS)
		
		# Change the node's client preferences.
		node.client_preferences.get('test', 'key', define=True)
		node.client_preferences.set('test', 'key', 'new value')
		
		self.assertEqual('new value', node.client_preferences.get('test', 'key'))
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self._event_handler.assert_has_calls([call.on_node_changed(node)])
	
	def test_client_preferences_init_set_from_storage(self):
		"""Tests setting the client preferences of a node loaded from storage."""
		node = self._create_node(notebook=self._notebook, client_preferences=DEFAULT_CLIENT_PREFERENCES, loaded_from_storage=True)
		self.assertEqual(DEFAULT_CLIENT_PREFERENCES, node.client_preferences._data)
		old_modified_time = node.modified_time
		sleep(1 * MS)
		
		# Change the node's client preferences.
		node.client_preferences.get('test', 'key', define=True)
		node.client_preferences.set('test', 'key', 'new value')

		self.assertEqual('new value', node.client_preferences.get('test', 'key'))
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self._event_handler.assert_has_calls([call.on_node_changed(node)])
	
	def test_client_preferences_create_copy(self):
		node = self._create_node(client_preferences=DEFAULT_CLIENT_PREFERENCES, loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.client_preferences, equal_to(node.client_preferences))
		assert_that(copy.client_preferences, is_not(same_instance(node.client_preferences)))
	
	def test_create_copy(self):
		node = self._create_node(notebook=self._create_notebook(), loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy._notebook, is_(none()))
		assert_that(copy.node_id, is_not(equal_to(node.node_id)))
		assert_that(copy.parent, is_(none()))
		assert_that(copy.is_dirty, equal_to(True))
	
	def test_create_copy_with_subtree(self):
		node = self._create_node(notebook=self._notebook, parent=None, loaded_from_storage=False)
		child1_copy = TestNotebookNode()
		child1 = TestNotebookNode()
		child1.set_create_copy_result(child1_copy)
		child2_copy = TestNotebookNode()
		child2 = TestNotebookNode()
		child2.set_create_copy_result(child2_copy)
		node._add_unbound_node_as_child(child1)
		node._add_unbound_node_as_child(child2)
		
		copy = node.create_copy(with_subtree=True)
		
		assert_that(copy.children), contains(child1_copy, child2_copy)
		self._event_handler.assert_has_calls([])


class ContentFolderNodeTestBase(ContentFolderTrashNodeTestBase):
	def test_is_trash(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		self.assertEqual(False, node.is_trash)
		
	def test_is_in_trash_1(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = False
		parent.is_in_trash = False
		
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		self.assertEqual(False, node.is_in_trash)
	
	def test_is_in_trash_2(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = True
		parent.is_in_trash = False
		
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		self.assertEqual(True, node.is_in_trash)
	
	def test_is_in_trash_3(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = False
		parent.is_in_trash = True
		
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		self.assertEqual(True, node.is_in_trash)
	
	def test_is_in_trash_4(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		
		self.assertEqual(False, node.is_in_trash)
	
	def test_title_set_if_deleted(self):
		parent = TestNotebookNode(notebook=self._notebook)
		node = self._create_node(notebook=self._notebook, parent=parent, title=DEFAULT_TITLE, loaded_from_storage=False)
		node.delete()
		
		with self.assertRaises(IllegalOperationError):
			node.title = 'new title'
		
		self.assertNotEquals('new title', node.title)
	
	def test_content_type_create_copy(self):
		
		node = self._create_node(loaded_from_storage=False)
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.content_type, equal_to(node.content_type))
	
	def test_add_new_node_as_child(self):
		node = self._create_node(notebook=self._notebook, loaded_from_storage=False)
		child = TestNotebookNode(notebook=None, parent=None)
		
		assert_that(node.can_add_new_node_as_child(), is_(True))
		
		node.add_new_node_as_child(child)
		
		assert_that(node.children, contains(child))
		assert_that(child._notebook, is_(same_instance(node._notebook)))
		assert_that(child.parent, is_(same_instance(node)))
		self._event_handler.assert_has_calls([call.on_node_added(child, parent=node)])
	
	def test_add_new_node_as_child_child_notebook_not_none(self):
		notebook = self._create_notebook()
		node = self._create_node(notebook=notebook, loaded_from_storage=False)
		child = TestNotebookNode(notebook=notebook, parent=None)
		
		with self.assertRaises(Exception):
			node.add_new_node_as_child(child)
		
		assert_that(node.children, is_not(contains(child)))
		assert_that(child._notebook, is_(same_instance(notebook)))
		assert_that(child.parent, is_(none()))
	
	def test_add_new_node_as_child_child_parent_not_none(self):
		notebook = self._create_notebook()
		node = self._create_node(notebook=notebook, loaded_from_storage=False)
		other_parent = TestNotebookNode()
		child = TestNotebookNode(parent=other_parent, add_to_parent=True)
		
		with self.assertRaises(Exception):
			node.add_new_node_as_child(child)
		
		assert_that(node.children, is_not(contains(child)))
		assert_that(child._notebook, is_(none()))
		assert_that(child.parent, is_(same_instance(other_parent)))
	
	def test_add_new_node_as_child_child_deleted(self):
		node = self._create_node(notebook=self._notebook, loaded_from_storage=False)
		child = TestNotebookNode()
		child.delete()
		
		with self.assertRaises(Exception):
			node.add_new_node_as_child(child)
		
		assert_that(node.children, is_not(contains(child)))
		assert_that(child._notebook, is_(none()))
		assert_that(child.parent, is_(none()))
	
	def test_add_new_node_as_child_node_deleted(self):
		notebook = self._create_notebook()
		parent = TestNotebookNode()
		node = self._create_node(notebook=notebook, parent=parent, loaded_from_storage=False)
		node.delete()
		child = TestNotebookNode()
		
		assert_that(node.can_add_new_node_as_child(), is_(False))
		
		with self.assertRaises(IllegalOperationError):
			node.add_new_node_as_child(child)
		
		assert_that(node.children, is_not(contains(child)))
		assert_that(child._notebook, is_(none()))
		assert_that(child.parent, is_(none()))
	
	def test_add_new_node_as_child_node_in_trash_1(self):
		notebook = self._create_notebook()
		parent = Mock(spec=NotebookNode)
		parent.is_trash = True
		parent.is_in_trash = False
		node = self._create_node(notebook=notebook, parent=parent, loaded_from_storage=False)
		child = TestNotebookNode(notebook=None, parent=None)
		
		assert_that(node.can_add_new_node_as_child(), is_(False))
		
		with self.assertRaises(IllegalOperationError):
			node.add_new_node_as_child(child)
		
		assert_that(node.children, is_not(contains(child)))
		assert_that(child._notebook, is_(none()))
		assert_that(child.parent, is_(none()))
	
	def test_add_new_node_as_child_node_in_trash_2(self):
		notebook = self._create_notebook()
		parent = Mock(spec=NotebookNode)
		parent.is_trash = False
		parent.is_in_trash = True
		node = self._create_node(notebook=notebook, parent=parent, loaded_from_storage=False)
		child = TestNotebookNode(notebook=None, parent=None)
		
		assert_that(node.can_add_new_node_as_child(), is_(False))
		
		with self.assertRaises(IllegalOperationError):
			node.add_new_node_as_child(child)
		
		assert_that(node.children, is_not(contains(child)))
		assert_that(child._notebook, is_(none()))
		assert_that(child.parent, is_(none()))
	
	def test_delete_without_children(self):
		parent = TestNotebookNode(notebook=self._notebook)
		node = self._create_node(notebook=self._notebook, parent=parent, loaded_from_storage=True)
		
		self.assertEqual(False, node.is_dirty)
		self.assertEqual(False, node.is_deleted)
		self.assertEqual(True, node.can_delete())
		
		node.delete()
		
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.is_deleted)
		self.assertEqual(False, node in parent.children)
		self.assertEqual(False, node in parent.get_children())
		self._event_handler.assert_has_calls([call.on_node_removed(node)])
	
	def test_delete_with_children(self):
		parent = TestNotebookNode(notebook=self._notebook)
		node = self._create_node(notebook=self._notebook, parent=parent, loaded_from_storage=True)
		child1 = Mock(spec=NotebookNode)
		child1.notebook = notebook=self._notebook
		child1.parent = node
		child2 = Mock(spec=NotebookNode)
		child2.notebook = notebook=self._notebook
		child2.parent = node
		node._add_child_node(child1)
		node._add_child_node(child2)
		
		node.delete()
		
		child1.delete.assert_called_with()
		child2.delete.assert_called_with()
# TODO: Nodig?		self.assertEqual([], node.children)
		self._event_handler.assert_has_calls([call.on_node_removed(node)])
	
	def test_delete_child_fails(self):
		parent = TestNotebookNode()
		node = self._create_node(parent=parent, loaded_from_storage=True)
		child = Mock(spec=NotebookNode)
		child.parent = node
		child.delete.side_effect = Exception()
		node._add_child_node(child)
		
		with self.assertRaises(Exception):
			node.delete()

# 		self.assertEqual(False, node.is_dirty)
		self.assertEqual(False, node.is_deleted)
		self.assertEqual(True, node in parent.children)
		self._event_handler.assert_has_calls([])
	
	def test_move(self):
		"""Tests moving a node."""
		# Create the node and parents.
		old_parent = TestNotebookNode(notebook=self._notebook)
		new_parent = TestNotebookNode(notebook=self._notebook)
		node = self._create_node(notebook=self._notebook, parent=old_parent, loaded_from_storage=True)
		old_modified_time = node.modified_time
		sleep(1 * MS)
		
		# Verify the node.
		self.assertEqual(True, node.can_move(new_parent))
		
		# Move the node.
		node.move(new_parent)
		
		# Verify the node and the parents.
		self.assertEqual(new_parent, node.parent)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self.assertEqual([], old_parent.children)
		self.assertEqual([node], new_parent.children)
		
		# Verify an event was raised.
		# TODO: Zorg dat er geen andere calls zijn
		self._event_handler.assert_has_calls([call.on_node_moved(node, old_parent=old_parent, new_parent=new_parent)])
	
	def test_move_behind_sibling(self):
		"""Tests moving a node behind a sibling."""
		
		# Create the node and parents.
		old_parent = TestNotebookNode(notebook=self._notebook)
		new_parent = TestNotebookNode(notebook=self._notebook)
		child1 = TestNotebookNode(notebook=self._notebook, parent=new_parent, add_to_parent=True)
		child2 = TestNotebookNode(notebook=self._notebook, parent=new_parent, add_to_parent=True)
		node = self._create_node(notebook=self._notebook, parent=old_parent, loaded_from_storage=True)
		
		# Move the node.
		node.move(new_parent, behind=child1)
		
		# Verify the new parent.
		self.assertEqual([child1, node, child2], new_parent.children)
	
	def test_move_behind_nonexistent_sibling(self):
		# Create the node and parents.
		old_parent = TestNotebookNode(notebook=self._notebook)
		new_parent = TestNotebookNode(notebook=self._notebook)
		node = self._create_node(notebook=self._notebook, parent=old_parent, loaded_from_storage=True)
		
		with self.assertRaises(IllegalOperationError):
			# Move the node.
			node.move(new_parent, behind=object())
		
		# Verify the node and the parents.
# 		self.assertEqual(False, node.is_dirty)
		self.assertEqual([node], old_parent.children)
		self.assertEqual([], new_parent.children)
		
		# Verify no event was raised.
		self._event_handler.assert_has_calls([])
	
	def test_move_if_deleted(self):
		"""Tests moving a node if it is deleted."""
		
		old_parent = TestNotebookNode(notebook=self._notebook)
		new_parent = TestNotebookNode(notebook=self._notebook)
		node = self._create_node(notebook=self._notebook, parent=old_parent, loaded_from_storage=True)
		node.delete()
		
		# Verify the node.
		self.assertEqual(False, node.can_move(new_parent))
		
		with self.assertRaises(IllegalOperationError):
			# Move the node.
			node.move(new_parent)
		
		# Verify the parent.
		self.assertEqual([], new_parent.children)
		
		# Verify no event was raised.
		self._event_handler.assert_has_calls([])
	
	def test_move_root(self):
		"""Tests moving a node if it is the root."""
		
		# Create the node and parents.
		new_parent = TestNotebookNode(notebook=self._notebook)
		node = self._create_node(notebook=self._notebook, parent=None, loaded_from_storage=True)
		
		# Verify the node.
		self.assertEqual(False, node.can_move(new_parent))
		
		with self.assertRaises(IllegalOperationError):
			# Move the node.
			node.move(new_parent)
		
		# Verify the node and the parent.
# 		self.assertEqual(False, node.is_dirty)
		self.assertEqual([], new_parent.children)
		
		# Verify no event was raised.
		self._event_handler.assert_has_calls([])
	
	def test_move_to_child(self):
		"""Tests moving a node to one of its children."""
		
		# Create the node and parents.
		old_parent = TestNotebookNode(notebook=self._notebook)
		node = self._create_node(notebook=self._notebook, parent=old_parent, loaded_from_storage=True)
		child1 = TestNotebookNode(notebook=self._notebook, parent=node, add_to_parent=True)
		child11 = TestNotebookNode(notebook=self._notebook, parent=child1, add_to_parent=True)
		new_parent = child11
		
		# Verify the node.
		self.assertEqual(False, node.can_move(new_parent))
		
		with self.assertRaises(IllegalOperationError):
			# Move the node.
			node.move(new_parent)
		
		# Verify the node and the parents.
# 		self.assertEqual(False, node.is_dirty)
		self.assertEqual([node], old_parent.children)
		self.assertEqual([], new_parent.children)
		
		# Verify no event was raised.
		self._event_handler.assert_has_calls([])
	
	def test_move_to_different_notebook(self):
		"""Tests moving a node to another notebook."""
		
		# Create the notebooks.
		notebook1 = Mock(spec=Notebook)
		notebook2 = Mock(spec=Notebook)
		
		# Create the node and parents.
		old_parent = Mock(spec=NotebookNode)
		node = self._create_node(notebook=notebook1, parent=old_parent, loaded_from_storage=True)
		old_parent.children = [node]
		new_parent = Mock(spec=NotebookNode)
		new_parent._notebook = notebook2
		new_parent.children = []

		# Verify the node.
		self.assertEqual(False, node.can_move(new_parent))
		
		with self.assertRaises(IllegalOperationError):
			# Move the node.
			node.move(new_parent, behind=object())
		
		# Verify the node and the parents.
# 		self.assertEqual(False, node.is_dirty)
		self.assertEqual([node], old_parent.children)
		self.assertEqual([], new_parent.children)
		
		# Verify no event was raised.
		self._event_handler.assert_has_calls([])


class ContentNodeTest(ContentFolderNodeTestBase, unittest.TestCase):
	def _create_node(
			self,
			notebook=None,
			parent=None,
			loaded_from_storage=False,
			title=DEFAULT_TITLE,
			order=DEFAULT_ORDER,
			icon_normal=DEFAULT_ICON_NORMAL,
			icon_open=DEFAULT_ICON_OPEN,
			title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
			title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
			client_preferences=DEFAULT_CLIENT_PREFERENCES,
			main_payload=DEFAULT,
			additional_payloads=DEFAULT,
			node_id=DEFAULT,
			created_time=DEFAULT,
			modified_time=DEFAULT,
			):
		
		if main_payload is DEFAULT:
			main_payload = TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA)
		if additional_payloads is DEFAULT:
			additional_payloads = [TestPayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA)]
		
		if loaded_from_storage:
			if node_id is DEFAULT:
				node_id = new_node_id()
			if created_time is DEFAULT:
				created_time = DEFAULT_CREATED_TIME
			if modified_time is DEFAULT:
				modified_time = DEFAULT_MODIFIED_TIME
		else:
			if node_id is DEFAULT:
				node_id = None
			if created_time is DEFAULT:
				created_time = None
			if modified_time is DEFAULT:
				modified_time = None
		
		node = ContentNode(
				notebook=notebook,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=parent,
				loaded_from_storage=loaded_from_storage,
				title=title,
				order=order,
				icon_normal=icon_normal,
				icon_open=icon_open,
				title_color_foreground=title_color_foreground,
				title_color_background=title_color_background,
				client_preferences=client_preferences,
				main_payload=main_payload,
				additional_payloads=additional_payloads,
				node_id=node_id,
				created_time=created_time,
				modified_time=modified_time,
				)
		if parent is not None:
			parent._add_child_node(node)
		return node
	
	def test_create_c(self):
		parent = TestNotebookNode()
		
		node = ContentNode(
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=parent,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				order=DEFAULT_ORDER,
				icon_normal=DEFAULT_ICON_NORMAL,
				icon_open=DEFAULT_ICON_OPEN,
				title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
				title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
				main_payload=TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
				additional_payloads=[TestPayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA)],
				)
		
		self.assertEqual(DEFAULT_HTML_PAYLOAD_NAME, node.main_payload_name)
		self.assertEqual([DEFAULT_PNG_PAYLOAD_NAME], node.additional_payload_names)
		self.assertEqual(DEFAULT_HTML_PAYLOAD_DATA, node.payloads[DEFAULT_HTML_PAYLOAD_NAME].open(mode='r').read())
		self.assertEqual(DEFAULT_PNG_PAYLOAD_DATA, node.payloads[DEFAULT_PNG_PAYLOAD_NAME].open(mode='r').read())
		
	def test_constructor_parameters_c1(self):
		with self.assertRaises(IllegalArgumentCombinationError):
			ContentNode(
					notebook=None,
					content_type=DEFAULT_CONTENT_TYPE,
					parent=None,
					loaded_from_storage=False,
					title=DEFAULT_TITLE,
					main_payload=None,  # Must be not None
					additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA)],
					node_id=None,
					)
	
	def test_constructor_parameters_c2(self):
		with self.assertRaises(IllegalArgumentCombinationError):
			ContentNode(
					notebook=None,
					content_type=DEFAULT_CONTENT_TYPE,
					parent=None,
					loaded_from_storage=False,
					title=DEFAULT_TITLE,
					main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
					additional_payloads=None,  # Must be not None
					node_id=None,
					)
	
	def test_add_additional_payload(self):
		node = ContentNode(
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				main_payload=TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
				additional_payloads=[TestPayload(DEFAULT_JPG_PAYLOAD_NAME, DEFAULT_JPG_PAYLOAD_DATA)],
				)
		old_modified_time = node.modified_time
		sleep(1 * MS)
		
		node.add_additional_payload(TestPayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA))
		
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self.assertEqual([DEFAULT_JPG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_NAME], node.additional_payload_names)
		self.assertEqual(DEFAULT_PNG_PAYLOAD_DATA, node.payloads[DEFAULT_PNG_PAYLOAD_NAME].open('r').read())		
	
	def test_remove_additional_payload(self):
		node = ContentNode(
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				main_payload=TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
				additional_payloads=[],
				)
		old_modified_time = node.modified_time
		sleep(1 * MS)
		
		node.add_additional_payload(TestPayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA))
		node.remove_additional_payload(DEFAULT_PNG_PAYLOAD_NAME)
		
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self.assertEqual([], node.additional_payload_names)
		with self.assertRaises(PayloadDoesNotExistError):
			node.get_payload(DEFAULT_PNG_PAYLOAD_NAME)
	
	def test_remove_additional_payload_nonexistent(self):
		node = ContentNode(
				notebook=None,
				node_id=DEFAULT_ID,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				main_payload=TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
				additional_payloads=[],
				)
		
		with self.assertRaises(PayloadDoesNotExistError):
			node.remove_additional_payload(DEFAULT_PNG_PAYLOAD_NAME)
		
# 		self.assertEqual(False, node.is_dirty)

class FolderNodeTest(ContentFolderNodeTestBase, unittest.TestCase):
	def _create_node(
			self,
			notebook=None,
			parent=None,
			loaded_from_storage=False,
			title=DEFAULT_TITLE,
			order=DEFAULT_ORDER,
			icon_normal=DEFAULT_ICON_NORMAL,
			icon_open=DEFAULT_ICON_OPEN,
			title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
			title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
			client_preferences=DEFAULT_CLIENT_PREFERENCES,
			node_id=DEFAULT,
			created_time=DEFAULT,
			modified_time=DEFAULT,
			):
		
		if loaded_from_storage:
			if node_id is DEFAULT:
				node_id = new_node_id()
			if created_time is DEFAULT:
				created_time = DEFAULT_CREATED_TIME
			if modified_time is DEFAULT:
				modified_time = DEFAULT_MODIFIED_TIME
		else:
			if node_id is DEFAULT:
				node_id = None
			if created_time is DEFAULT:
				created_time = None
			if modified_time is DEFAULT:
				modified_time = None
		
		node = FolderNode(
				notebook=notebook,
				parent=parent,
				loaded_from_storage=loaded_from_storage,
				title=title,
				order=order,
				icon_normal=icon_normal,
				icon_open=icon_open,
				title_color_foreground=title_color_foreground,
				title_color_background=title_color_background,
				client_preferences=client_preferences,
				node_id=node_id,
				created_time=created_time,
				modified_time=modified_time,
				)
		if parent is not None:
			parent._add_child_node(node)
		return node


class TrashNodeTest(ContentFolderTrashNodeTestBase, unittest.TestCase):
	def _create_node(
			self,
			notebook=None,
			parent=None,
			loaded_from_storage=False,
			title=DEFAULT_TITLE,
			order=DEFAULT_ORDER,
			icon_normal=DEFAULT_ICON_NORMAL,
			icon_open=DEFAULT_ICON_OPEN,
			title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
			title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
			client_preferences=DEFAULT_CLIENT_PREFERENCES,
			node_id=DEFAULT,
			created_time=DEFAULT,
			modified_time=DEFAULT,
			):
		
		if loaded_from_storage:
			if node_id is DEFAULT:
				node_id = new_node_id()
			if created_time is DEFAULT:
				created_time = DEFAULT_CREATED_TIME
			if modified_time is DEFAULT:
				modified_time = DEFAULT_MODIFIED_TIME
		else:
			if node_id is DEFAULT:
				node_id = None
			if created_time is DEFAULT:
				created_time = None
			if modified_time is DEFAULT:
				modified_time = None
		
		node = TrashNode(
				notebook=notebook,
				parent=parent,
				loaded_from_storage=loaded_from_storage,
				title=title,
				order=order,
				icon_normal=icon_normal,
				icon_open=icon_open,
				title_color_foreground=title_color_foreground,
				title_color_background=title_color_background,
				client_preferences=client_preferences,
				node_id=node_id,
				created_time=created_time,
				modified_time=modified_time,
				)
		if parent is not None:
			parent._add_child_node(node)
		return node
	
	def test_is_trash(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		self.assertEqual(True, node.is_trash)
		
	def test_is_in_trash(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = False
		parent.is_in_trash = False
		
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		self.assertEqual(False, node.is_in_trash)
	
	def test_delete(self):
		# Create the node, the parent and the child.
		parent = TestNotebookNode()
		node = TrashNode(
				notebook=None,
				node_id=DEFAULT_ID,
				parent=parent,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				)
		parent._add_child_node(node)
		child = Mock(spec=NotebookNode)
		child.parent = node
		node._add_child_node(child)
		
		self.assertEqual(False, node.can_delete())
				
		with self.assertRaises(IllegalOperationError):
			node.delete()
		
		self.assertEqual(False, child.delete.called)
## TODO: Nodig?		self.assertEqual([child], node.children)
# 		self.assertEqual(False, node.is_dirty)
		self.assertEqual(False, node.is_deleted)
	
	def test_move(self):
		"""Tests moving a node."""
		
		# Create the node and parents.
		old_parent = Mock(spec=NotebookNode)
		node = self._create_node(parent=old_parent, loaded_from_storage=True)
		old_parent.children = [node]
		new_parent = Mock(spec=NotebookNode)
		new_parent._notebook = None
		new_parent.parent = None
		new_parent.children = []
		
		# Verify the node.
		self.assertEqual(False, node.can_move(new_parent))
		
		with self.assertRaises(IllegalOperationError):
			# Move the node.
			node.move(new_parent)
		
		# Verify the node and the parents.
		self.assertEqual(old_parent, node.parent)
# 		self.assertEqual(False, node.is_dirty)
		self.assertEqual([node], old_parent.children)
		self.assertEqual([], new_parent.children)
	
	# NEW COPYING ---
	
	def test_class_create_copy(self):
		node = self._create_node(loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy, instance_of(FolderNode))
	
	def test_content_type_create_copy(self):
		node = self._create_node(loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.content_type, equal_to(CONTENT_TYPE_FOLDER))
		
	def test_add_new_node_as_child(self):
		notebook = self._create_notebook()
		node = self._create_node(notebook=notebook, loaded_from_storage=False)
		child = TestNotebookNode(notebook=None, parent=None)
		
		assert_that(node.can_add_new_node_as_child(), is_(False))
		
		with self.assertRaises(IllegalOperationError):
			node.add_new_node_as_child(child)
		
		assert_that(node.children, is_not(contains(child)))
		assert_that(child._notebook, is_(none()))
		assert_that(child.parent, is_(none()))
	

# Utilities

class AnyUuidMatcher(object):
	def __eq__(self, other):
		if other is None:
			return False
		matcher = re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', other)
		return matcher is not None
	
	def __repr__(self, *_args, **_kwargs):
		return '{cls}[]'.format(cls=self.__class__.__name__, **self.__dict__)

class AllButOneUuidMatcher(AnyUuidMatcher):
	def __init__(self, uuid):
		self.uuid = uuid
	
	def __eq__(self, other):
		return super(AllButOneUuidMatcher, self).__eq__(other) and other != self.uuid

class AttributeMatcher(object):
	def __init__(self, attribute, expected_value):
		self.attribute = attribute
		self.expected_value = expected_value
	
	def __eq__(self, other):
		if self.attribute not in other:
			return False
		result = other[self.attribute] == self.expected_value
		return result
	
	def __ne__(self, other):
		return not self.__eq__(other);

class FileMatcher(object):
	def __init__(self, expected):
		self.expected = expected.read()
	
	def __eq__(self, other):
		actual = other.read()
		return self.expected == actual
	
	def __ne__(self, other):
		return not self.__eq__(other);

class MissingAttributeMatcher(object):
	def __init__(self, attribute):
		self.attribute = attribute
	
	def __eq__(self, other):
		return self.attribute not in other
	
	def __ne__(self, other):
		return not self.__eq__(other);

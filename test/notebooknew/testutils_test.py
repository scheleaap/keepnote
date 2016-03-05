# -*- coding: utf-8 -*-

from __future__ import absolute_import
import unittest

from keepnote.notebooknew import new_node_id
from test.notebooknew import ContentFolderNodeTestBase

from .testutils import *

CONTENT_TYPE_TEST = u'application/x-notebook-test-node'

class TestNotebookNodeTest(unittest.TestCase, ContentFolderNodeTestBase):
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
		
		node = TestNotebookNode(
				notebook=notebook,
				parent=parent,
				add_to_parent=False,
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

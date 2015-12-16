# -*- coding: utf-8 -*-

import base64
import copy
from datetime import datetime
import io
#import mock
#from mock import Mock, call
import os
import re
from pytz import utc
import unittest

from keepnote.notebooknew import *
from keepnote.notebooknew import CONTENT_TYPE_HTML, CONTENT_TYPE_TRASH, CONTENT_TYPE_FOLDER
from keepnote.notebooknew.dao import Dao
import keepnote.notebooknew.storage as storage
from keepnote.notebooknew.storage import StoredNode
import keepnote.notebooknew.storage.mem
from keepnote.pref import Pref

from utils import *

PARENT_ID_ATTRIBUTE = 'parent_id'
MAIN_PAYLOAD_NAME_ATTRIBUTE = 'main_payload_name'
TITLE_ATTRIBUTE = 'title'
CREATED_TIME_ATTRIBUTE = 'created_time'
MODIFIED_TIME_ATTRIBUTE = 'modified_time'
ORDER_ATTRIBUTE = 'order'
ICON_NORMAL_ATTRIBUTE = 'icon'
ICON_OPEN_ATTRIBUTE = 'icon_open'
TITLE_COLOR_FOREGROUND_ATTRIBUTE = 'title_fgcolor'
TITLE_COLOR_BACKGROUND_ATTRIBUTE = 'title_bgcolor'
CLIENT_PREFERENCES_ATTRIBUTE = 'client_preferences'

DEFAULT=object()
DEFAULT_ID = 'my_id'
DEFAULT_CONTENT_TYPE = CONTENT_TYPE_HTML
DEFAULT_TITLE = 'my_title'
DEFAULT_CREATED_TIMESTAMP = 1012615322
DEFAULT_CREATED_TIME = datetime.fromtimestamp(DEFAULT_CREATED_TIMESTAMP, tz=utc)
DEFAULT_MODIFIED_TIMESTAMP = 2000000000
DEFAULT_MODIFIED_TIME = datetime.fromtimestamp(DEFAULT_MODIFIED_TIMESTAMP, tz=utc)
DEFAULT_ORDER = 12
DEFAULT_ICON_NORMAL = 'node_red_closed.png'
DEFAULT_ICON_OPEN = 'node_red_open.png'
DEFAULT_TITLE_COLOR_FOREGROUND = '#ffffff'
DEFAULT_TITLE_COLOR_BACKGROUND = '#ff0000'
DEFAULT_PAYLOAD_NAMES = ['my_payload1', 'my_payload2']
DEFAULT_HTML_PAYLOAD_NAME = os.path.basename('index.html')
DEFAULT_HTML_PAYLOAD = base64.b64decode('PCFET0NUWVBFIGh0bWw+DQoNCjxoMT5UZXN0IE5vZGU8L2gxPg0KPHA+VGhpcyBpcyBhIG5vZGUgdXNlZCBmb3IgdGVzdGluZy48L3A+DQo=')
DEFAULT_PNG_PAYLOAD_NAME = os.path.basename('image1.png')
DEFAULT_PNG_PAYLOAD = base64.b64decode('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')
DEFAULT_JPG_PAYLOAD_NAME = os.path.basename('image2.jpg')
DEFAULT_JPG_PAYLOAD = base64.b64decode('/9j/4AAQSkZJRgABAQEAYwBjAAD/4QBmRXhpZgAATU0AKgAAAAgABAEaAAUAAAABAAAAPgEbAAUAAAABAAAARgEoAAMAAAABAAMAAAExAAIAAAAQAAAATgAAAAAAAJhXAAAD6AAAmFcAAAPocGFpbnQubmV0IDQuMC41AP/bAEMAAgEBAgEBAgICAgICAgIDBQMDAwMDBgQEAwUHBgcHBwYHBwgJCwkICAoIBwcKDQoKCwwMDAwHCQ4PDQwOCwwMDP/bAEMBAgICAwMDBgMDBgwIBwgMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDP/AABEIABcAIAMBIgACEQEDEQH/xAAfAAABBQEBAQEBAQAAAAAAAAAAAQIDBAUGBwgJCgv/xAC1EAACAQMDAgQDBQUEBAAAAX0BAgMABBEFEiExQQYTUWEHInEUMoGRoQgjQrHBFVLR8CQzYnKCCQoWFxgZGiUmJygpKjQ1Njc4OTpDREVGR0hJSlNUVVZXWFlaY2RlZmdoaWpzdHV2d3h5eoOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4eLj5OXm5+jp6vHy8/T19vf4+fr/xAAfAQADAQEBAQEBAQEBAAAAAAAAAQIDBAUGBwgJCgv/xAC1EQACAQIEBAMEBwUEBAABAncAAQIDEQQFITEGEkFRB2FxEyIygQgUQpGhscEJIzNS8BVictEKFiQ04SXxFxgZGiYnKCkqNTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqCg4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2dri4+Tl5ufo6ery8/T19vf4+fr/2gAMAwEAAhEDEQA/APvzRNBs9S1NZJIGVMFSVzhWHC54HHBP41X0ya18T3McdosjszbREwwyg4ALbh29TgY71kfF/wCOujfDrwLfWuktJq3iiZJobHSrd/8ASLm4GNysoOVUdSzEKAQxO35q0/2bnjufhzo8kNnaabcyWRge3RgDE0YEbdBhsFTz3znPNfMYTEww04whaUtW9P6/I9DEYOdeg6s7xWiWv5rr9+5k/GO90L4R+G0i164SzuLq9gtxc+YFSPdPGPlcgqODnJGcBiOlaHhe9h8XeFo7m223drlltZ4G3m5RGKbmPHzZU52ggnPHavGP2uvib4fuNX1Dw/8A8Jhpmm+KdJsIb+ysJLFp11Nl3ypEJtp8v7ueBjD85Aq78Lv2idK1T4hxx2GnWeiNfMbS4ja5MgmUSSbGChF5OMqTg4J964q2c1vrHtWlZ6XW/wA/6R308jh9U5Lu61s9vl/TPP8A4M/ALxT4b8Mx3nie+GveMNRYzPO1/JF9gCoqIvmqCzsfn3nkECNVwqAV3ds+teBJpdQ0G4vtXvpw9mYrjUZPnVzkjc/CjKknHJPQ0UV8ZGtL2j+f6H0tSvJxV9n06Hj3xA/ZDvPiD4xt9X1fbbzSxKJE+1NOGcEgABidi42ggM3O4gjOKz4vggP2c70Xkr+JNc3N9osjFcofskygoobzJ0J3Bzkj+6OnOSis8POUua52VMXUfLB7H//Z')

# The following StoredNodes and NotebookNodes have the following structure:
# root
#   child1
#     child11
#     child12
#       child121
#   child2
#     child21
ROOT_SN = StoredNode('root_id', CONTENT_TYPE_TEST, attributes={TITLE_ATTRIBUTE: 'root'}, payloads=[])
CHILD1_SN = StoredNode('child1_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'child1'}, payloads=[])
CHILD11_SN = StoredNode('child11_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'child1_id', TITLE_ATTRIBUTE: 'child11'}, payloads=[])
CHILD12_SN = StoredNode('child12_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'child1_id', TITLE_ATTRIBUTE: 'child12'}, payloads=[])
CHILD121_SN = StoredNode('child121_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'child12_id', TITLE_ATTRIBUTE: 'child121'}, payloads=[])
CHILD2_SN = StoredNode('child2_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'child2'}, payloads=[])
CHILD21_SN = StoredNode('child21_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'child2_id', TITLE_ATTRIBUTE: 'child21'}, payloads=[])
TRASH_SN = StoredNode('trash_id', CONTENT_TYPE_TRASH, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'trash'}, payloads=[])


def datetime_to_timestamp(dt):
	# From https://docs.python.org/3.3/library/datetime.html#datetime.datetime.timestamp
	return (dt - datetime(1970, 1, 1, tzinfo=utc)).total_seconds()


class DaoTest(unittest.TestCase):
	def test_new_in_local(self):
		root = TestNode()
		child1 = TestNode(parent=root, add_to_parent=True)
		child2 = TestNode(parent=root, add_to_parent=True)
		
		notebook = Notebook()
		notebook.root = root
		storage = keepnote.notebooknew.storage.mem.InMemoryStorage()
		node_daos = { TestNode: TestNodeDao() }
		dao = Dao(notebook, storage, node_daos)
		
		dao.sync()
		
		self.assertEquals(node_dao.to_stored_node(root), storage.get_node(root.node_id))
		self.assertEquals(node_dao.to_stored_node(child1), storage.get_node(child1.node_id))
		self.assertEquals(node_dao.to_stored_node(child2), storage.get_node(child2.node_id))
	
	def test_new_in_remote(self):
		notebook = Notebook()
		storage = keepnote.notebooknew.storage.mem.InMemoryStorage()
		storage.add_node(ROOT_SN)
		storage.add_node(CHILD1_SN)
		storage.add_node(CHILD2_SN)
		node_daos = { TestNode: TestNodeDao(storage) }
		dao = Dao(notebook, storage, node_daos)
		
		dao.sync()
		
		root_nn = notebook.root
		child1_nn = notebook.root.get_children()[0]
		child2_nn = notebook.root.get_children()[1]
		self.assertEqual(node_dao.to_notebook_node(ROOT_SN).node, root) PROBLEEM: parent vs parent_id?! Idee: NotebookNodes een parent_id en children_ids geven, en alleen die bij __eq__ gebruiken
		self.assertEqual(node_dao.to_notebook_node(CHILD1_SN).node, child1_nn)
		self.assertEqual(node_dao.to_notebook_node(CHILD2_SN).node, child2_nn)

Ideeen:
- een Payload-klasse maken voor StoredNode, die wel/niet gevuld kan zijn. payload_names kan dan daaruit worden gegenereerd


if __name__ == '__main__':
	unittest.main()
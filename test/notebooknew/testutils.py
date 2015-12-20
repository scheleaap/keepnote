# -*- coding: utf-8 -*-
import base64
from datetime import datetime
import hashlib
import io
import os
from pytz import utc

from keepnote.notebooknew import CONTENT_TYPE_HTML
from keepnote.notebooknew import NotebookNode, NotebookNodePayload, IllegalOperationError
from keepnote.notebooknew import new_node_id
from keepnote.notebooknew.dao import ReadFromStorageWriteToMemoryPayload
from keepnote.notebooknew.storage import NotebookStorage

__all__ = [
		'CONTENT_TYPE_TEST',
		'DEFAULT',
		'DEFAULT_ID',
		'DEFAULT_CONTENT_TYPE',
		'DEFAULT_TITLE',
		'DEFAULT_CREATED_TIMESTAMP',
		'DEFAULT_CREATED_TIME',
		'DEFAULT_MODIFIED_TIMESTAMP',
		'DEFAULT_MODIFIED_TIME',
		'DEFAULT_ORDER',
		'DEFAULT_ICON_NORMAL',
		'DEFAULT_ICON_OPEN',
		'DEFAULT_TITLE_COLOR_FOREGROUND',
		'DEFAULT_TITLE_COLOR_BACKGROUND',
		'DEFAULT_CLIENT_PREFERENCES',
		'DEFAULT_PAYLOAD_NAMES',
		'DEFAULT_HTML_PAYLOAD_NAME',
		'DEFAULT_HTML_PAYLOAD_DATA',
		'DEFAULT_HTML_PAYLOAD_HASH',
		'DEFAULT_PNG_PAYLOAD_NAME',
		'DEFAULT_PNG_PAYLOAD_DATA',
		'DEFAULT_PNG_PAYLOAD_HASH',
		'DEFAULT_JPG_PAYLOAD_NAME',
		'DEFAULT_JPG_PAYLOAD_DATA',
		'DEFAULT_JPG_PAYLOAD_HASH',
		'TestNotebookNode',
		'TestPayload',
		'ReadOnlyInMemoryStorage',
		]

CONTENT_TYPE_TEST = u'application/x-notebook-test-node'

DEFAULT=object()
DEFAULT_ID = 'my_id'
DEFAULT_CONTENT_TYPE = CONTENT_TYPE_HTML
DEFAULT_TITLE = 'my_title'
DEFAULT_CREATED_TIMESTAMP = 1012615322
DEFAULT_CREATED_TIME = datetime.fromtimestamp(DEFAULT_CREATED_TIMESTAMP, tz=utc)
DEFAULT_MODIFIED_TIMESTAMP = 1020000000
DEFAULT_MODIFIED_TIME = datetime.fromtimestamp(DEFAULT_MODIFIED_TIMESTAMP, tz=utc)
DEFAULT_ORDER = 12
DEFAULT_ICON_NORMAL = 'node_red_closed.png'
DEFAULT_ICON_OPEN = 'node_red_open.png'
DEFAULT_TITLE_COLOR_FOREGROUND = '#ffffff'
DEFAULT_TITLE_COLOR_BACKGROUND = '#ff0000'
DEFAULT_CLIENT_PREFERENCES = { 'test': { 'key': 'value' }}
DEFAULT_PAYLOAD_NAMES = ['my_payload1', 'my_payload2']
DEFAULT_HTML_PAYLOAD_NAME = os.path.basename('index.html')
DEFAULT_HTML_PAYLOAD_DATA = base64.b64decode('PCFET0NUWVBFIGh0bWw+DQoNCjxoMT5UZXN0IE5vZGU8L2gxPg0KPHA+VGhpcyBpcyBhIG5vZGUgdXNlZCBmb3IgdGVzdGluZy48L3A+DQo=')
DEFAULT_HTML_PAYLOAD_HASH = hashlib.md5(DEFAULT_HTML_PAYLOAD_DATA).hexdigest()
DEFAULT_PNG_PAYLOAD_NAME = os.path.basename('image1.png')
DEFAULT_PNG_PAYLOAD_DATA = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAACAAAAArCAIAAACW3x1gAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAYdEVYdFNvZnR3YXJlAHBhaW50Lm5ldCA0LjAuNWWFMmUAAAWNSURBVFhHrZdZSJVbFMdPYC+ZFKQvolKkZWqa10pIozIaMH1QKSsVUbPBMKciCSrLsCIVnPA6oA8WXIu8ZYUQKikqVwK7zTRro5Y2mGk4nfvz7O139Zzv6Dnd+3s4rPXt/Z3/ntZa+9NodbS1td2+ffvu3bvnz58/efJkZmbmzp07a2trMU6dOlVVVbVr167g4GD6iP6moxkdHQ0PD1+yZMncuXPnzJnj7u6O7efnFxkZqRln3rx5ixcvxpg/f758z2Q0WVlZCxYsEH80Y8aMhQsXWlhYuLm5paennzlz5ty5c4WFhdglJSXNzc379++X75mM5vjx42fPnv1Lx5MnT+RjNX78+MHMEBsaGsLlt6urSzRNgSY+Pp6hSW9KLly4wBRTUlKGh4dx169fz6Tr6upEqzE069atk+Z0sFs+Pj6XLl2qqKioqak5ffo0k379+rVsNoKpAp8/f161atWRI0f+HufatWtRUVFFRUViQsbQF2CY7e3tjx8/HhkZkY90BAYGNjY2SmcCrDBTkY4akwQYF6fTyspq9uzZ0dHR7Kp4jl5oaKiw9fj586eDgwO/0jfgX4H6+vrly5c/evQIm+FnZ2d//fpVNOXl5bW0tAibkHz16hWzBPGEYCQShW2IFGCvFi1adPny5T91XL9+XTQLWH1loVn6/Pz8Y8eOJSYmiif37t1LTU0VtiFjAqz7smXLrl69SlaIi4vjqHAW+/r6ZBet1tvbW1pqIJCQkCAdA8YEWOLVq1cL//v37+ynsBX0nih7IyguLmZA0jFgTICkxgxEfA4ODuqtD9CqHKovX76sXLlS2II9e/YYvqIwJtDR0WFpaUnmERrAv1RXVwsbAgICrly5Iuzk5GRSHqsqXI6GjY3NFKEgN5k42rBhg729fWxsrLOzc0RExMQQpXXjxo1btmzhr9mhoKCggwcPkrpPnDjBmeZoyH5qSAHBp0+f3r9/P3F7FRgjTUTDhw8fPn78GBYWtl0Hp1b20C0vffRiYpKAId++fWtqapKOVktuYPWko4M/JQeTxqki/v7+HAcnJydKFi+KDlMJPHz4kP08evSo9CcI9PT03Lx5k/9l/w8dOkS1GBgYEH2QJBu6urreunUL16gAC8W/s8oTdxsBAo2VoSJxeB48eCAbDHjz5s2sWbNQNSrAaSEBUF7evn2Lyx6UlZUx/RUrVtCkuk965OTklJeXqws0NDRwkDBCQkKEAAfp8OHDlDDlgE5LZ2fn5s2bVQT6+/sZaW9vLzarLASAIBcPTWfHjh0qAklJSaQzYZNHlUJNoiUUbty4IVxTWLt2rb4AS+Hp6akcsosXL3LtEDawyZRiouHZs2fykXH27dtHBdQXSEtLKygokI4uZ9BBSSEIMILKysqlS5cibGzFCHKiXVQ6fQFqDkXtNx3c5l68eEGm5GiKViUOqEUIMFc60+H3cejAxvLinTt3xCsallVYQJRbW1u3traSM3CfP3/u4eHB0lMP2HmeKAIKHCri8Y9xyJuyYZyxi5dyLyLRc0Xkoufr68vQeCLigDXZu3cvrqHAtGgoRkq2efr0KVdHVhm7tLSU4Nq0aRMCDJOUuW3bNjKumIrpjM1AESA+Z86cuXv37tzcXIo+KfPAgQNKZNHKPVXYpjNJgCG7uLiQxUgSYG5YqTJJADi5fCJI5/9AExMT8/LlS+np7i+Ojo7379+X/n9GJVVwYbazs5v22mwiKgLA0WaHqc+EAi5XOaoCtUXvwmIKU30VUU+4wXFro6gRmSIyzEV9BqpQG6RlDqYKUALXrFkjHXMwQ0DUOHPRkFelOSW/LkAy8PLy4vNRYevWrRkZGZRlePfunej36wJczSgyXDH5vMHv7u7GBmoZQc73vq2tLV+TpHG+lsQ7ZqDV/gOanoppyROYaQAAAABJRU5ErkJggg==')
DEFAULT_PNG_PAYLOAD_HASH = hashlib.md5(DEFAULT_PNG_PAYLOAD_DATA).hexdigest()
DEFAULT_JPG_PAYLOAD_NAME = os.path.basename('image2.jpg')
DEFAULT_JPG_PAYLOAD_DATA = base64.b64decode('/9j/4AAQSkZJRgABAQEAYwBjAAD/4QBmRXhpZgAATU0AKgAAAAgABAEaAAUAAAABAAAAPgEbAAUAAAABAAAARgEoAAMAAAABAAMAAAExAAIAAAAQAAAATgAAAAAAAJhXAAAD6AAAmFcAAAPocGFpbnQubmV0IDQuMC41AP/bAEMAAgEBAgEBAgICAgICAgIDBQMDAwMDBgQEAwUHBgcHBwYHBwgJCwkICAoIBwcKDQoKCwwMDAwHCQ4PDQwOCwwMDP/bAEMBAgICAwMDBgMDBgwIBwgMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDP/AABEIABcAIAMBIgACEQEDEQH/xAAfAAABBQEBAQEBAQAAAAAAAAAAAQIDBAUGBwgJCgv/xAC1EAACAQMDAgQDBQUEBAAAAX0BAgMABBEFEiExQQYTUWEHInEUMoGRoQgjQrHBFVLR8CQzYnKCCQoWFxgZGiUmJygpKjQ1Njc4OTpDREVGR0hJSlNUVVZXWFlaY2RlZmdoaWpzdHV2d3h5eoOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4eLj5OXm5+jp6vHy8/T19vf4+fr/xAAfAQADAQEBAQEBAQEBAAAAAAAAAQIDBAUGBwgJCgv/xAC1EQACAQIEBAMEBwUEBAABAncAAQIDEQQFITEGEkFRB2FxEyIygQgUQpGhscEJIzNS8BVictEKFiQ04SXxFxgZGiYnKCkqNTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqCg4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2dri4+Tl5ufo6ery8/T19vf4+fr/2gAMAwEAAhEDEQA/APvzRNBs9S1NZJIGVMFSVzhWHC54HHBP41X0ya18T3McdosjszbREwwyg4ALbh29TgY71kfF/wCOujfDrwLfWuktJq3iiZJobHSrd/8ASLm4GNysoOVUdSzEKAQxO35q0/2bnjufhzo8kNnaabcyWRge3RgDE0YEbdBhsFTz3znPNfMYTEww04whaUtW9P6/I9DEYOdeg6s7xWiWv5rr9+5k/GO90L4R+G0i164SzuLq9gtxc+YFSPdPGPlcgqODnJGcBiOlaHhe9h8XeFo7m223drlltZ4G3m5RGKbmPHzZU52ggnPHavGP2uvib4fuNX1Dw/8A8Jhpmm+KdJsIb+ysJLFp11Nl3ypEJtp8v7ueBjD85Aq78Lv2idK1T4hxx2GnWeiNfMbS4ja5MgmUSSbGChF5OMqTg4J964q2c1vrHtWlZ6XW/wA/6R308jh9U5Lu61s9vl/TPP8A4M/ALxT4b8Mx3nie+GveMNRYzPO1/JF9gCoqIvmqCzsfn3nkECNVwqAV3ds+teBJpdQ0G4vtXvpw9mYrjUZPnVzkjc/CjKknHJPQ0UV8ZGtL2j+f6H0tSvJxV9n06Hj3xA/ZDvPiD4xt9X1fbbzSxKJE+1NOGcEgABidi42ggM3O4gjOKz4vggP2c70Xkr+JNc3N9osjFcofskygoobzJ0J3Bzkj+6OnOSis8POUua52VMXUfLB7H//Z')
DEFAULT_JPG_PAYLOAD_HASH = hashlib.md5(DEFAULT_JPG_PAYLOAD_DATA).hexdigest()


class TestNotebookNode(NotebookNode):
	"""A testing implementation of NotebookNode."""

	def __init__(self, notebook_storage=None, notebook=None, parent=None, add_to_parent=None, loaded_from_storage=True, title=DEFAULT_TITLE, node_id=None):
		if node_id is None:
			node_id = new_node_id()
		super(TestNotebookNode, self).__init__(
				notebook_storage=notebook_storage,
				notebook=notebook,
				content_type=CONTENT_TYPE_TEST,
				parent=parent,
				loaded_from_storage=loaded_from_storage,
				title=title,
				node_id=node_id,
				)
		
		self._is_deleted = False
		self._is_dirty = False
		self._is_in_trash = False
		
		if self.parent is not None:
			if add_to_parent is None:
				raise IllegalOperationError('Please pass add_to_parent')
			elif add_to_parent == True:
				self.parent._add_child_node(self)
	
	@property
	def is_dirty(self):
		return self._is_dirty
	
	@property
	def is_in_trash(self):
		return False
	
	@property
	def is_root(self):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	@property
	def is_trash(self):
		return False
	
	def set_is_deleted(self, value):
		self.is_deleted = value
	
	def set_is_dirty(self, value):
		self._is_dirty = value
	
	def set_is_in_trash(self, value):
		self._is_in_trash = value


class TestPayload(NotebookNodePayload):
	def __init__(self, name, data):
		super(TestPayload, self).__init__(name=name)
		self.data = data
		self._md5hash = hashlib.md5(self.data).hexdigest()
	
	def copy(self):
		return TestPayload(self.name, self.data)
	
	def get_md5hash(self):
		return self._md5hash
	
	def open(self, mode='r'):
		if mode == 'w':
			def on_close(data):
				self.data = data
				self._md5hash = hashlib.md5(self.data).hexdigest()
			return ReadFromStorageWriteToMemoryPayload.CapturingBytesIO(on_close)
		else:
			return io.BytesIO(self.data)
		
	def __eq__(self, other):
		return \
			isinstance(other, self.__class__) and \
			self.name == other.name and \
			self.data == other.data

	def __ne__(self, other):
		return not self.__eq__(other);

class ReadOnlyInMemoryStorage(NotebookStorage):
	def __init__(self, backing_storage, read_only=True):
		self.backing_storage = backing_storage
		self.read_only = read_only
	
	def add_node(self, *args, **kwargs):
		if self.read_only: raise ReadOnlyError()
		return self.backing_storage.add_node(*args, **kwargs)

	def add_node_payload(self, *args, **kwargs):
		if self.read_only: raise ReadOnlyError()
		return self.backing_storage.add_node_payload(*args, **kwargs)
	
	def get_all_nodes(self, *args, **kwargs):
		return self.backing_storage.get_all_nodes(*args, **kwargs)
	
	def get_node(self, *args, **kwargs):
		return self.backing_storage.get_node(*args, **kwargs)

	def get_node_payload(self, *args, **kwargs):
		return self.backing_storage.get_node_payload(*args, **kwargs)
	
	def get_notebook(self, *args, **kwargs):
		return self.backing_storage.get_notebook(*args, **kwargs)
	
	def has_node(self, *args, **kwargs):
		return self.backing_storage.has_node(*args, **kwargs)
	
	def has_node_payload(self, *args, **kwargs):
		return self.backing_storage.has_node_payload(*args, **kwargs)
		
	def remove_node(self, *args, **kwargs):
		if self.read_only: raise ReadOnlyError()
		return self.backing_storage.remove_node(*args, **kwargs)
		
	def remove_node_payload(self, *args, **kwargs):
		if self.read_only: raise ReadOnlyError()
		return self.backing_storage.remove_node_payload(*args, **kwargs)
	
	def set_node_attributes(self, *args, **kwargs):
		if self.read_only: raise ReadOnlyError()
		return self.backing_storage.set_node_attributes(*args, **kwargs)
		
	def set_notebook_attributes(self, *args, **kwargs):
		if self.read_only: raise ReadOnlyError()
		return self.backing_storage.set_notebook_attributes(*args, **kwargs)

	def __repr__(self):
		return '{cls}[]'.format(cls=self.__class__.__name__, **self.__dict__)

class ReadOnlyError(Exception):
	pass

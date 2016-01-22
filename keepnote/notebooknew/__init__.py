
from collections import namedtuple, OrderedDict
from datetime import datetime
import io
import os
from pytz import utc
import sys
import uuid

from keepnote.listening import Listeners
from keepnote.pref import Pref
from keepnote.notebook import AttrDef

__all__ = [
		'Notebook',
		'NotebookNode',
		'NotebookNodePayload',
		'ContentNode',
		'FolderNode',
		'TrashNode',
		'NotebookError',
		'IllegalArgumentCombinationError',
		'IllegalOperationError',
		'InvalidStructureError',
		'NodeDoesNotExistError',
		'PayloadAlreadyExistsError',
		'PayloadDoesNotExistError'
		]

# Content types
CONTENT_TYPE_HTML = u'text/html'
CONTENT_TYPE_TRASH = u'application/x-notebook-trash'
CONTENT_TYPE_FOLDER = u'application/x-notebook-dir'
#CONTENT_TYPE_UNKNOWN = u'application/x-notebook-unknown'

# Attribute definitions
AttributeDefinition = namedtuple('AttributeDefinition', ['key', 'type', 'default'], verbose=False)
PARENT_ID_ATTRIBUTE = AttributeDefinition('parent_id', type='string', default=None)
MAIN_PAYLOAD_NAME_ATTRIBUTE = AttributeDefinition('main_payload_name', type='string', default=None)
TITLE_ATTRIBUTE = AttributeDefinition('title', type='string', default='Untitled node')
CREATED_TIME_ATTRIBUTE = AttributeDefinition('created_time', type='timestamp', default=None)
MODIFIED_TIME_ATTRIBUTE = AttributeDefinition('modified_time', type='timestamp', default=None)
ORDER_ATTRIBUTE = AttributeDefinition('order', type='int', default=sys.maxint)
ICON_NORMAL_ATTRIBUTE = AttributeDefinition('icon', type='string', default=None)
ICON_OPEN_ATTRIBUTE = AttributeDefinition('icon_open', type='string', default=None)
TITLE_COLOR_FOREGROUND_ATTRIBUTE = AttributeDefinition('title_fgcolor', type='string', default=None)
TITLE_COLOR_BACKGROUND_ATTRIBUTE = AttributeDefinition('title_bgcolor', type='string', default=None)
CLIENT_PREFERENCES_ATTRIBUTE = AttributeDefinition('client_preferences', type='dict', default={})

# New nodes
NEW_CONTENT_TYPE = CONTENT_TYPE_HTML
NEW_PAYLOAD_NAME = 'page.html'
NEW_PAYLOAD_DATA = u"""
<!doctype html>
<html>
<meta charset="utf-8">
<title>title</title>
"""

def datetime_to_timestamp(dt):
	# From https://docs.python.org/3.3/library/datetime.html#datetime.datetime.timestamp
	return (dt - datetime(1970, 1, 1, tzinfo=utc)).total_seconds()

def get_attribute_value(attribute_definition, attributes):
	"""Returns the value of an attribute from a dictionary of strings, using the specified attribute definition.
	
	@param attribute_definition: The AttributeDefinition that specifies the attribute's key, type and default value.
	@param attributes: The attributes to get the value from.
	@return: attributes[attribute_definition.key] converted to the proper type if it exists in attributes, else attribute_definition.default
	"""
	if attribute_definition.key in attributes:
		string_value = attributes[attribute_definition.key]
		if attribute_definition.type == 'string':
			return string_value
		elif attribute_definition.type == 'int':
			return int(string_value)
		elif attribute_definition.type == 'timestamp':
			dt = datetime.fromtimestamp(int(string_value), tz=utc)
			return dt
	else:
		return attribute_definition.default

def new_node_id():
	"""Generate a new, random node id."""
	return unicode(uuid.uuid4())

class Notebook(object):
	"""A collection of nodes.
	
	@ivar root: The root NotebookNode.
	@ivar trash: TODO
	@ivar client_preferences: A Pref containing the notebook's client preferences.
	@ivar node_changed_listeners: TODO
	@ivar closing_listeners: TODO
	@ivar close_listeners: TODO
	@ivar is_dirty: TODO
	"""
	
	def __init__(self):
		"""Constructor.
		"""
		self.root = None
		self.trash = None
		self.client_preferences = Pref()
		self.node_changed_listeners = Listeners()
		self.closing_listeners = Listeners()
		self.close_listeners = Listeners()
		self._client_event_listeners = {}
	
	def close(self):
		self.closing_listeners.notify()
		self.close_listeners.notify()
	
	def get_client_event_listeners(self, key):
		"""Returns a custom event listeners object for the notebook's client, creating it if necessary.
		
		@param key The key of the event listeners object.
		@return A Listener.
		"""
		if key not in self._client_event_listeners:
			self._client_event_listeners[key] = Listeners()
		return self._client_event_listeners[key]
	
	def get_node_by_id(self, node_id):
		"""Returns a node from the notebook.
		
		@param node_id: The id of the node.
		@return A NotebookNode.
		@raise NodeDoesNotExistError: If a node with the id does not exist.
		"""
		for node in self._traverse_tree():
			if node.node_id == node_id:
				return node
		raise NodeDoesNotExistError(node_id)
	
	def has_node(self, node_id):
		"""Returns whether a node exists within the notebook.
		
		@param node_id: The id of the node.
		@return Whether a node exists within the notebook.
		"""
		for node in self._traverse_tree():
			if node.node_id == node_id:
				return True
		return False
	
	@property
	def is_dirty(self):
		"""TODO"""
		return any([node.is_dirty for node in self._traverse_tree()])
	
	def _traverse_tree(self):
		"""A generator method that yields all NotebookNodes in the notebook."""
		nodes_to_visit = []
		if self.root is not None:
			nodes_to_visit.append(self.root)
		while nodes_to_visit:
			node = nodes_to_visit.pop()
			yield node
			for child in node.get_children():
				nodes_to_visit.append(child)
		

class NotebookNode(object):
	"""A node in a notebook. Every node has an identifier, a content type and a title.
	
	@ivar notebook: TODO
	@ivar node_id: The id of the node.
	@ivar children: The node's children that have not been deleted and are waiting to be saved. TODO
	@ivar content_type: The content type of the node.
	@ivar parent: The parent of the node.
	@ivar title: The title of the node.
	@ivar created_time: TODO
	@ivar modified_time: TODO
	@ivar order: TODO
	@ivar icon_normal: TODO
	@ivar icon_open: TODO
	@ivar title_color_foreground: TODO
	@ivar title_color_background: TODO
	@ivar client_preferences: TODO
	@ivar is_dirty: Indicates whether the node has changed since it was last saved.
	@ivar is_deleted: Indicates whether the node has been deleted from the notebook.
	"""
	
	class StorageChange(object):
		"""Represents a change that needs to be made in a NotebookStorage."""
		
		def __init__(self, name):
			self.name = name
		
		def __repr__(self):
			return '{cls}[{name}]'.format(cls=self.__class__.__name__, **self.__dict__)
	
	# Change constants
	DUMMY_CHANGE = StorageChange('DUMMY_CHANGE')
	NEW = StorageChange('NEW')
	DELETED = StorageChange('DELETED')
	CHANGED_TITLE = StorageChange('CHANGED_TITLE')
	CHANGED_ICON_NORMAL = StorageChange('CHANGED_ICON_NORMAL')
	CHANGED_ICON_OPEN = StorageChange('CHANGED_ICON_OPEN')
	CHANGED_MODIFIED_TIME = StorageChange('CHANGED_MODIFIED_TIME')
	CHANGED_CLIENT_PREFERENCES = StorageChange('CHANGED_CLIENT_PREFERENCES')
	MOVED = StorageChange('MOVED')

	def __init__(
			self,
			notebook,
			content_type,
			parent,
			loaded_from_storage,
			title,
			order=None,
			icon_normal=None,
			icon_open=None,
			title_color_foreground=None,
			title_color_background=None,
			client_preferences=None,
			node_id=None,
			created_time=None,
			modified_time=None
			):
		"""Constructor.
		
		@param notebook: The notebook the node is in.
		@param content_type: The content type of node.
		@param parent: The parent of the node or None.
		@param loaded_from_storage: TODO
		@param title: The title of the node.
		@param order: TODO
		@param icon_normal: TODO
		@param icon_open: TODO
		@param title_color_foreground: TODO
		@param title_color_background: TODO
		@param client_preferences: TODO
		@param node_id: The id of the new node. Only if loaded_from_storage == True.
		@param created_time: The creation time of the new node. Only if loaded_from_storage == True.
		@param modified_time: The last modification time of the new node. Only if loaded_from_storage == True.
		"""
		self._notebook = notebook
		self._children = []
		self.content_type = content_type
		self.parent = parent
		self._title = title
		self.order = order
		self._icon_normal = icon_normal
		self._icon_open = icon_open
		self._title_color_foreground = title_color_foreground
		self._title_color_background = title_color_background
		self.client_preferences = Pref(client_preferences)
		self.client_preferences.change_listeners.add(self._on_client_preferences_change)
		self.is_deleted = False
		
		if loaded_from_storage:
			if node_id is None:
				raise IllegalArgumentCombinationError()
			self.node_id = node_id
			self._created_time = created_time
			self._modified_time = modified_time
			self.is_dirty = False
		else:
			if node_id is not None:
				raise IllegalArgumentCombinationError()
			if created_time is not None:
				raise IllegalArgumentCombinationError()
			if modified_time is not None:
				raise IllegalArgumentCombinationError()
			self.node_id = new_node_id()
			self._created_time = datetime.now(tz=utc)
			self._modified_time = self._created_time
			self.is_dirty = True

	def _add_child_node(self, child_node):
		"""DEPRECATED. Use _add_unbound_node_as_child() instead."""
		self._children.append(child_node)
		assert child_node.parent is self
	
	def add_new_node_as_child(self, child_node):
		"""Adds a new node as a child of this node.
		
		The new node may be a copy of an existing node and may even be a subtree.
		
		The new node must not have a notebook and a parent.
		
		This method may only be called if this node is not deleted and is not in the trash. 
		
		@param child_node: The node to add as a child.
		@raise ValueError: If the child node's notebook or parent are not None.
		@raise IllegalOperationError: If the node on which this method is called is deleted or is in the trash.
		"""
		raise NotImplementedError('TODO')
	
	def _add_unbound_node_as_child(self, child_node):
		"""Adds a node as a child of this node.
		
		The new node must not have a notebook and a parent.
		
		@param child_node: The node to add as a child. The node's notebook and parent must be unset.
		@raise ValueError: If the child node's notebook or parent are not None.
		"""
		if child_node._notebook is not None:
			raise ValueError('Trying to add a node as a child that has a notebook')
		if child_node.parent is not None:
			raise ValueError('Trying to add a node as a child that has a parent')
		self._children.append(child_node)
		child_node._notebook = self._notebook
		child_node.parent = self
	
	def can_add_new_node_as_child(self):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	def can_copy(self, target, with_subtree):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	def can_delete(self):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	def can_move(self, target):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	@property
	def children(self):
		"""TODO"""
		return self.get_children()
	
	def copy(self, target, with_subtree, behind=None):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	def create_copy(self, with_subtree):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	@property
	def created_time(self):
		return self._created_time
	
	def delete(self):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	@property
	def icon_normal(self):
		return self._icon_normal
	
	@icon_normal.setter
	def icon_normal(self, icon_normal):
		if self.is_deleted:
			raise IllegalOperationError('Cannot set the normal icon of a deleted node')
		
		self._icon_normal = icon_normal
		self.modified_time = datetime.now(tz=utc)
	
	@property
	def icon_open(self):
		return self._icon_open
	
	@icon_open.setter
	def icon_open(self, icon_open):
		if self.is_deleted:
			raise IllegalOperationError('Cannot set the open icon of a deleted node')
		
		self._icon_open = icon_open
		self.modified_time = datetime.now(tz=utc)
	
	def is_node_a_child(self, node):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	@property
	def is_in_trash(self):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	@property
	def is_root(self):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	@property
	def is_trash(self):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	def get_children(self):
		"""TODO"""
		return [child for child in self._children]
	
	def has_children(self):
		"""TODO"""
		return len(self.get_children()) > 0
	
	@property
	def modified_time(self):
		return self._modified_time
	
	# TODO: Remove?
	@modified_time.setter
	def modified_time(self, modified_time):
		# TODO: Untested
		if self.is_deleted:
			raise IllegalOperationError('Cannot set the modified time of a deleted node')
		
		self._modified_time = modified_time
	
	def move(self, target, behind=None):
		"""TODO
		
		Cannot be used to move a node to another workbook. Use copy() for that instead.
		"""
		raise NotImplementedError('TODO')
	
	@property
	def notebook(self):
		return self._notebook
	
	def _on_client_preferences_change(self):
		self.modified_time = datetime.now(tz=utc)
	
	def _remove_child_node(self, child_node):
		assert child_node in self._children
		self._children.remove(child_node)
		
	@property
	def title(self):
		return self._title
	
	@title.setter
	def title(self, title):
		if self.is_deleted:
			raise IllegalOperationError('Cannot set the title of a deleted node')
		
		self._title = title
		self.modified_time = datetime.now(tz=utc)
	
	@property
	def title_color_background(self):
		return self._title_color_background
	
	@title_color_background.setter
	def title_color_background(self, title_color_background):
		if self.is_deleted:
			raise IllegalOperationError('Cannot set the title background color of a deleted node')
		
		self._title_color_background = title_color_background
		self.modified_time = datetime.now(tz=utc)
	
	@property
	def title_color_foreground(self):
		return self._title_color_foreground
	
	@title_color_foreground.setter
	def title_color_foreground(self, title_color_foreground):
		if self.is_deleted:
			raise IllegalOperationError('Cannot set the title foreground color of a deleted node')
		
		self._title_color_foreground = title_color_foreground
		self.modified_time = datetime.now(tz=utc)


class NotebookNodePayload(object):
	"""A payload of a node.
	
	@ivar name: The name of the payload.
	"""
	
	def __init__(self, name):
		"""Constructor.
		
		@param name: The name of the payload.
		"""
		self.name = name
	
	def copy(self):
		"""Copies the NotebookNodePayload.
		
		@return: A new, equivalent NotebookNodePayload object.
		"""
		raise NotImplementedError(self.copy.__name__)
	
	def get_md5hash(self):
		"""Returns the current hash of the payload data.
		
		This may provide an efficient way of comparing payload data, but it may also involve opening and reading the payload.
		@return: The hash of the current payload data. 
		"""
		raise NotImplementedError(self.get_md5hash.__name__)
		
	def open(self, mode='r'):
		"""Opens the payload data.
		
		@param mode: Specifies the mode in which the payload data must be opened. 'r' specifies (binary) reading, 'w' specifies (binary) writing.
		@return: An object implementing IOBase.
		"""
		raise NotImplementedError(self.open.__name__)


class AbstractContentFolderNode(NotebookNode):
	"""A base class for content and folder nodes in a notebook.
	"""
	
	def add_new_node_as_child(self, child_node):
		if self.is_in_trash:
			raise IllegalOperationError('Cannot add a child to a node in the trash')
		if self.is_deleted:
			raise IllegalOperationError('Cannot add a child to a deleted node')
		if child_node.is_deleted:
			raise IllegalOperationError('Trying to add a deleted node as a child')
		self._add_unbound_node_as_child(child_node)
	
	def can_add_new_node_as_child(self):
		if self.is_in_trash or self.is_deleted:
			return False
		else:
			return True
	
	def can_copy(self, target, with_subtree):
		if self.is_deleted:
			return False
		elif target.is_trash or target.is_in_trash:
			return False
		elif with_subtree and self.is_node_a_child(target):
			return False
		else:
			return True
	
	def can_delete(self):
		return not self.is_root
	
	def can_move(self, target):
		return \
				not self.is_deleted and \
				self._notebook == target._notebook and \
				not self.is_root and \
				not self.is_node_a_child(target)
	
	def delete(self):
		"""TODO"""
		if self.parent is None:
			raise IllegalOperationError('Cannot delete the root node')
		for child in self._children:
			child.delete()
		self.parent._remove_child_node(self)
		self.is_deleted = True
	
	def is_node_a_child(self, node):
		p = node.parent
		while p is not None:
			if p == self:
				return True
			else:
				p = p.parent
		return False
	
	@property
	def is_in_trash(self):
		if self.parent is not None:
			return self.parent.is_trash or self.parent.is_in_trash
		return False
	
	@property
	def is_root(self):
		return self.parent is None
		
	@property
	def is_trash(self):
		return False
	
	def move(self, target, behind=None):
		if self.is_deleted:
			raise IllegalOperationError('Cannot move a deleted node')
		elif self._notebook != target._notebook:
			raise IllegalOperationError('Cannot move a note to a node in another notebook')
		elif self.is_root:
			raise IllegalOperationError('Cannot move the root node')
		elif self.is_node_a_child(target):
			raise IllegalOperationError('Cannot move a node to one of its children')
		
		if behind is None:
			target._children.append(self)
		else:
			try:
				i = target._children.index(behind)
				target._children.insert(i + 1, self)
			except ValueError as e:
				raise IllegalOperationError('Unknown child', e)
		self.parent._children.remove(self)
		self.parent = target
		
		self.modified_time = datetime.now(tz=utc)


class ContentNode(AbstractContentFolderNode):
	"""A node with content in a notebook. Every content node has at least one payload and may have additional payloads.

	TODO:
	@ivar main_payload_name
	@ivar additional_payload_names: The names of the payloads of the node.
	@ivar payloads
	"""
	
	# Change constants
	PAYLOAD_CHANGE = NotebookNode.StorageChange('PAYLOAD_CHANGE')
	
	# Idea: Use classmethods for loading from storage / for creating new in memory

	def __init__(
			self,
			notebook,
			content_type,
			parent,
			loaded_from_storage,
			title,
			order=None,
			icon_normal=None,
			icon_open=None,
			title_color_foreground=None,
			title_color_background=None,
			client_preferences=None,
			main_payload=None,
			additional_payloads=None,
			node_id=None,
			created_time=None,
			modified_time=None,
			):
		"""Constructor.
		
		Either main_payload and additional_payloads or main_payload_name and additional_payload_names must be passed.
		
		@param notebook: The notebook the node is in.
		@param content_type: The content type of node.
		@param parent: The parent of the node or None.
		@param loaded_from_storage: TODO
		@param main_payload: A ContentNodePayload object.
		@param title: The title of the node.
		@param order: TODO
		@param icon_normal: TODO
		@param icon_open: TODO
		@param title_color_foreground: TODO
		@param title_color_background: TODO
		@param additional_payloads: A list containing ContentNodePayload objects.
		@param node_id: The id of the node. Only if loaded_from_storage == True.
		@param created_time: The creation time of the new node. Only if loaded_from_storage == True.
		@param modified_time: The last modification time of the new node. Only if loaded_from_storage == True.
		"""
		super(ContentNode, self).__init__(
				notebook=notebook,
				content_type=content_type,
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
		if loaded_from_storage:
			if node_id is None or main_payload is None or additional_payloads is None:
				raise IllegalArgumentCombinationError()
		else:
			if node_id is not None or main_payload is None or additional_payloads is None:
				raise IllegalArgumentCombinationError()
		
		if main_payload is not None: # TODO Remove
			self.main_payload_name = main_payload.name
			self.payloads = { main_payload.name: main_payload }
		self.additional_payload_names = []
		if additional_payloads is not None:
			for additional_payload in additional_payloads:
				self.additional_payload_names.append(additional_payload.name)
				self.payloads[additional_payload.name] = additional_payload
	
	def add_additional_payload(self, payload):
		"""Adds an additional payload.
		
		@param payload: A ContentNodePayload object.
		@raise PayloadAlreadyExistsError: If the node already has a payload with the same name.
		"""
		if payload.name == self.main_payload_name:
			raise PayloadAlreadyExistsError('A payload with the name "{name}" already exists'.format(name=payload.name))
		elif payload.name in self.additional_payload_names:
			raise PayloadAlreadyExistsError('A payload with the name "{name}" already exists'.format(name=payload.name))
		
		self.additional_payload_names.append(payload.name)
		self.payloads[payload.name] = payload
		
		self.modified_time = datetime.now(tz=utc)
	
	def copy(self, target, with_subtree, behind=None):
		if self.is_deleted:
			raise IllegalOperationError('Cannot copy a deleted node')
		elif target.is_trash or target.is_in_trash:
			raise IllegalOperationError('Cannot copy a node to the trash')
		elif with_subtree and self.is_node_a_child(target):
			raise IllegalOperationError('Cannot copy a node with its children to a child')
		
		copy = target.new_content_child_node(
				content_type=self.content_type,
				title=self._title,
				main_payload=self.payloads[self.main_payload_name].copy(),
				additional_payloads=[self.payloads[additional_payload_name].copy() for additional_payload_name in self.additional_payload_names],
				behind=behind
				)
		if with_subtree:
			for child in self._children:
				if not child.is_deleted:
					child.copy(copy, with_subtree=with_subtree)
		
		return copy
	
	def create_copy(self, with_subtree):
		copy = ContentNode(
				notebook=None,
				content_type=self.content_type,
				parent=None,
				title=self.title,
				icon_normal=self.icon_normal,
				icon_open=self.icon_open,
				title_color_foreground=self.title_color_foreground,
				title_color_background=self.title_color_background,
				client_preferences=self.client_preferences._data,
				loaded_from_storage=False,
				main_payload=self.payloads[self.main_payload_name].copy(),
				additional_payloads=[self.payloads[additional_payload_name].copy() for additional_payload_name in self.additional_payload_names],
				)
		if with_subtree:
			for child in self._children:
				if not child.is_deleted:
					child_copy = child.create_copy(with_subtree=with_subtree)
					copy.add_new_node_as_child(child_copy)
		
		return copy
	
	def get_payload(self, payload_name):
		"""Returns a payload.
		
		@param payload_name: The name of the payload to add.
		@return: A ContentNodePayload object.
		@raise PayloadDoesNotExistError: If the node does not have a payload with the given name.
		"""
		if payload_name in self.payloads:
			return self.payloads[payload_name]
		else:
			raise PayloadDoesNotExistError(payload_name)
	
	def remove_additional_payload(self, payload_name):
		"""Removes a payload.
		
		@param payload_name: The name of the payload to remove.
		@raise PayloadDoesNotExistError: If the node does not have a payload with the given name.
		"""
		if payload_name in self.payloads:
			self.additional_payload_names.remove(payload_name)
			del self.payloads[payload_name]
		else:
			raise PayloadDoesNotExistError(payload_name)
		
		self.modified_time = datetime.now(tz=utc)
	
	def __repr__(self):
		return '{cls}[{node_id}, {content_type}, {_title}]'.format(
				cls=self.__class__.__name__,
				dirty='*' if self.is_dirty else '-',
				**self.__dict__
				)


class FolderNode(AbstractContentFolderNode):
	"""A folder node in a notebook. A folder node has no content.
	"""

	def __init__(self,
			notebook,
			parent,
			loaded_from_storage,
			title,
			order=None,
			icon_normal=None,
			icon_open=None,
			title_color_foreground=None,
			title_color_background=None,
			client_preferences=None,
			node_id=None,
			created_time=None,
			modified_time=None,
			):
		"""Constructor.
		
		@param notebook: The notebook the node is in.
		@param parent: The parent of the node or None.
		@param loaded_from_storage: TODO
		@param title: The title of the node.
		@param order: TODO
		@param icon_normal: TODO
		@param icon_open: TODO
		@param title_color_foreground: TODO
		@param title_color_background: TODO
		@param node_id: The id of the node. Only if loaded_from_storage == True.
		@param created_time: The creation time of the new node. Only if loaded_from_storage == True.
		@param modified_time: The last modification time of the new node. Only if loaded_from_storage == True.
		"""
		super(FolderNode, self).__init__(
				notebook=notebook,
				content_type=CONTENT_TYPE_FOLDER,
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
		if loaded_from_storage:
			if node_id is None:
				raise IllegalArgumentCombinationError()
		else:
			if node_id is not None:
				raise IllegalArgumentCombinationError()
	
	def copy(self, target, with_subtree, behind=None):
		if self.is_deleted:
			raise IllegalOperationError('Cannot copy a deleted node')
		elif target.is_trash or target.is_in_trash:
			raise IllegalOperationError('Cannot copy a node to the trash')
		elif with_subtree and self.is_node_a_child(target):
			raise IllegalOperationError('Cannot copy a node with its children to a child')
		
		copy = target.new_folder_child_node(
				title=self._title,
				behind=behind
				)
		if with_subtree:
			for child in self._children:
				if not child.is_deleted:
					child.copy(copy, with_subtree=with_subtree)
		
		return copy
	
	def create_copy(self, with_subtree):
		copy = FolderNode(
				notebook=None,
				parent=None,
				title=self.title,
				icon_normal=self.icon_normal,
				icon_open=self.icon_open,
				title_color_foreground=self.title_color_foreground,
				title_color_background=self.title_color_background,
				client_preferences=self.client_preferences._data,
				loaded_from_storage=False,
				)
		if with_subtree:
			for child in self._children:
				if not child.is_deleted:
					child_copy = child.create_copy(with_subtree=with_subtree)
					copy.add_new_node_as_child(child_copy)
		
		return copy
	
	def __repr__(self):
		return '{cls}[{node_id}, {_title}]'.format(
				cls=self.__class__.__name__,
				dirty='*' if self.is_dirty else '-',
				**self.__dict__
				)

class TrashNode(NotebookNode):
	"""A trash node in a notebook. A trash node has no content.
	"""

	def __init__(self,
			notebook,
			parent,
			loaded_from_storage,
			title,
			order=None,
			icon_normal=None,
			icon_open=None,
			title_color_foreground=None,
			title_color_background=None,
			client_preferences=None,
			node_id=None,
			created_time=None,
			modified_time=None,
			):
		"""Constructor.
		
		@param notebook: The notebook the node is in.
		@param parent: The parent of the node or None.
		@param loaded_from_storage: TODO
		@param title: The title of the node.
		@param order: TODO
		@param icon_normal: TODO
		@param icon_open: TODO
		@param title_color_foreground: TODO
		@param title_color_background: TODO
		@param node_id: The id of the node. Only if loaded_from_storage == True.
		@param created_time: The creation time of the new node. Only if loaded_from_storage == True.
		@param modified_time: The last modification time of the new node. Only if loaded_from_storage == True.
		"""
		super(TrashNode, self).__init__(
				notebook=notebook,
				content_type=CONTENT_TYPE_TRASH,
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
		if loaded_from_storage:
			if node_id is None:
				raise IllegalArgumentCombinationError()
		else:
			if node_id is not None:
				raise IllegalArgumentCombinationError()

	def add_new_node_as_child(self, child_node):
		raise IllegalOperationError('Cannot add a child node to the trash')
		
	def can_add_new_node_as_child(self):
		return False
	
	def can_copy(self, target, with_subtree):
		if target.is_trash or target.is_in_trash:
			return False
		elif self.is_node_a_child(target):
			return False
		else:
			return True
	
	def can_delete(self):
		return False
	
	def can_move(self, target):
		return False
	
	def copy(self, target, with_subtree, behind=None):
		if self.is_deleted:
			raise IllegalOperationError('Cannot copy a deleted node')
		elif target.is_trash or target.is_in_trash:
			raise IllegalOperationError('Cannot copy a node to the trash')
		elif self.is_node_a_child(target):
			raise IllegalOperationError('Cannot copy the trash node to a child')
		
		copy = target.new_folder_child_node(
				title=self._title,
				behind=behind
				)
		if with_subtree:
			for child in self._children:
				if not child.is_deleted:
					child.copy(copy, with_subtree=with_subtree)
		
		return copy
	
	def create_copy(self, with_subtree):
		copy = FolderNode(
				notebook=None,
				parent=None,
				title=self.title,
				icon_normal=self.icon_normal,
				icon_open=self.icon_open,
				title_color_foreground=self.title_color_foreground,
				title_color_background=self.title_color_background,
				client_preferences=self.client_preferences._data,
				loaded_from_storage=False,
				)
		if with_subtree:
			for child in self._children:
				if not child.is_deleted:
					child_copy = child.create_copy(with_subtree=with_subtree)
					copy.add_new_node_as_child(child_copy)
		
		return copy
	
	def delete(self):
		raise IllegalOperationError('Cannot delete the trash node')
	
	def is_node_a_child(self, node):
		p = node.parent
		while p is not None:
			if p == self:
				return True
			else:
				p = p.parent
		return False
	
	@property
	def is_in_trash(self):
		return False
	
	@property
	def is_root(self):
		return self.parent is None
		
	@property
	def is_trash(self):
		return True
	
	def move(self, target, behind=None):
		raise IllegalOperationError('Cannot move the trash node')
	
	def __repr__(self):
		return '{cls}[{node_id}, {_title}]'.format(
				cls=self.__class__.__name__,
				dirty='*' if self.is_dirty else '-',
				**self.__dict__
				)
	

class NotebookError(Exception):
	pass


class IllegalArgumentCombinationError(Exception):
	pass


class IllegalOperationError(NotebookError):
	pass


class InvalidStructureError(NotebookError):
	pass


class NodeDoesNotExistError(NotebookError):
	pass


class PayloadAlreadyExistsError(NotebookError):
	pass


class PayloadDoesNotExistError(NotebookError):
	pass

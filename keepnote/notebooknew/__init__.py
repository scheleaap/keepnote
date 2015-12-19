
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
from keepnote.notebooknew.storage import StoredNode

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
	
	def __init__(self, notebook_storage=None):
		"""Constructor.
		
		@param notebook_storage: The NotebookStorage to use. 
		"""
		self._notebook_storage = notebook_storage
		self.root = None
		self.trash = None
		self.client_preferences = Pref()
		self.node_changed_listeners = Listeners()
		self.closing_listeners = Listeners()
		self.close_listeners = Listeners()
		self._client_event_listeners = {}
		
		if notebook_storage is not None:
			self._init_from_storage()
	
	def close(self):
		self.closing_listeners.notify()
		self.save()
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
	
	def has_node(self, node_id, unsaved_deleted=True):
		"""Returns whether a node exists within the notebook.
		
		@param node_id: The id of the node.
		@return Whether a node exists within the notebook.
		"""
		for node in self._traverse_tree():
			if node.node_id == node_id and (unsaved_deleted == True or (unsaved_deleted == False and not node.is_deleted)):
				return True
		return False
	
	def _init_from_storage(self):
		"""Initializes the Notebook from the NotebookStorage."""

		# Load all StoredNodes.		
		stored_nodes = list(self._notebook_storage.get_all_nodes())
		
		# Create NotebookNodes for all StoredNotes and index all StoredNotes and NotebookNodes by id.
		nodes_by_id = {}
		for stored_node in stored_nodes:
			title = get_attribute_value(TITLE_ATTRIBUTE, stored_node.attributes)
			created_time = get_attribute_value(CREATED_TIME_ATTRIBUTE, stored_node.attributes)
			modified_time = get_attribute_value(MODIFIED_TIME_ATTRIBUTE, stored_node.attributes)
			order = get_attribute_value(ORDER_ATTRIBUTE, stored_node.attributes)
			icon_normal = get_attribute_value(ICON_NORMAL_ATTRIBUTE, stored_node.attributes)
			icon_open = get_attribute_value(ICON_OPEN_ATTRIBUTE, stored_node.attributes)
			title_color_foreground = get_attribute_value(TITLE_COLOR_FOREGROUND_ATTRIBUTE, stored_node.attributes)
			title_color_background = get_attribute_value(TITLE_COLOR_BACKGROUND_ATTRIBUTE, stored_node.attributes)
			
			if stored_node.content_type == CONTENT_TYPE_FOLDER:
				notebook_node = FolderNode(
						notebook_storage=self._notebook_storage,
						notebook=self,
						parent=None,
						loaded_from_storage=True,
						title=title,
						order=order,
						icon_normal=icon_normal,
						icon_open=icon_open,
						title_color_foreground=title_color_foreground,
						title_color_background=title_color_background,
						node_id=stored_node.node_id,
						created_time=created_time,
						modified_time=modified_time,
						)
			elif stored_node.content_type == CONTENT_TYPE_TRASH:
				notebook_node = TrashNode(
						notebook_storage=self._notebook_storage,
						notebook=self,
						parent=None,
						loaded_from_storage=True,
						title=title,
						order=order,
						icon_normal=icon_normal,
						icon_open=icon_open,
						title_color_foreground=title_color_foreground,
						title_color_background=title_color_background,
						node_id=stored_node.node_id,
						created_time=created_time,
						modified_time=modified_time,
						)
			else:
				if not stored_node.payload_names:
					raise InvalidStructureError('Content node {node_id} has no payload'.format(
							node_id=stored_node.node_id))
					
				main_payload_name = get_attribute_value(MAIN_PAYLOAD_NAME_ATTRIBUTE, stored_node.attributes)
				
				if main_payload_name is None:
					raise InvalidStructureError('Missing attribute \'{attribute}\' in content node {node_id}'.format(
							node_id=stored_node.node_id,
							attribute=MAIN_PAYLOAD_NAME_ATTRIBUTE.key))
				elif main_payload_name not in stored_node.payload_names:
					raise InvalidStructureError(
							'The main payload with name \'{main_payload_name}\' is missing in content node {node_id}'.format(
									node_id=stored_node.node_id,
									main_payload_name=main_payload_name))
				
				additional_payload_names = [payload_name for payload_name in stored_node.payload_names if payload_name != main_payload_name]
				notebook_node = ContentNode(
						notebook_storage=self._notebook_storage,
						notebook=self,
						content_type=stored_node.content_type,
						parent=None,
						loaded_from_storage=True,
						title=title,
						order=order,
						icon_normal=icon_normal,
						icon_open=icon_open,
						title_color_foreground=title_color_foreground,
						title_color_background=title_color_background,
						node_id=stored_node.node_id,
						created_time=created_time,
						modified_time=modified_time,
						main_payload_name=main_payload_name,
						additional_payload_names=additional_payload_names,
						)
			nodes_by_id[stored_node.node_id] = (stored_node, notebook_node)
		
		# Create the NotebookNode tree structure.
		for stored_node, notebook_node in nodes_by_id.values():
			parent_id = get_attribute_value(PARENT_ID_ATTRIBUTE, stored_node.attributes)
			if parent_id is not None:
				if parent_id not in nodes_by_id:
					raise InvalidStructureError('Node {child_id} has no parent {parent_id}'.format(
							child_id=stored_node.node_id, parent_id=parent_id))
				elif parent_id == stored_node.node_id:
					raise InvalidStructureError('Node {node_id} references itself as parent'.format(
							node_id=stored_node.node_id))
				else:
					# Check for cycles.
					temp_parent_notebook_node = nodes_by_id[parent_id][1]
					while temp_parent_notebook_node.parent is not None:
						temp_parent_notebook_node = temp_parent_notebook_node.parent
						
						if temp_parent_notebook_node.node_id == stored_node.node_id:
							raise InvalidStructureError('Node {node_id} indirectly references itself as parent'.format(
									node_id=stored_node.node_id))
					
				parent_notebook_node = nodes_by_id[parent_id][1]
				notebook_node.parent = parent_notebook_node
				parent_notebook_node._add_child_node(notebook_node)
			else:
				if self.root is not None:
					raise InvalidStructureError('Multiple root nodes found')
				self.root = notebook_node
			if notebook_node.content_type == CONTENT_TYPE_TRASH:
				self.trash = notebook_node
		
		# If no root node exists, create it.
		if self.root is None:
			notebook_node = FolderNode(
					notebook_storage=self._notebook_storage,
					notebook=self,
					parent=None,
					title=TITLE_ATTRIBUTE.default,
					loaded_from_storage=False
					)
			self.root = notebook_node

		# If no trash node exists, create it.
		if self.trash is None:
			notebook_node = TrashNode(
					notebook_storage=self._notebook_storage,
					notebook=self,
					parent=self.root,
					title=TITLE_ATTRIBUTE.default,
					loaded_from_storage=False
					)
			self.root._add_child_node(notebook_node)
			self.trash = notebook_node
		
		if self.trash.parent is not self.root:
			raise InvalidStructureError('The trash node is not a direct child of the root node')
		
		# Sort children by their id.
		for stored_node, notebook_node in nodes_by_id.values():
			notebook_node._children.sort(key=lambda child_notebook_node: child_notebook_node.node_id)
	
	@property
	def is_dirty(self):
		"""TODO"""
		return any([node.is_dirty for node in self._traverse_tree()])
	
	def save(self):
		"""Saves all changes to the notebook."""
		self._save_node(self.root)
	
	def _save_node(self, node):
		"""TODO"""
		for child in node.get_children(not_deleted=False, unsaved_deleted=True):
			self._save_node(child)
		
		node.save()
		
		for child in node.get_children(not_deleted=True, unsaved_deleted=False):
			self._save_node(child)
	
	def _traverse_tree(self):
		"""A generator method that yields all NotebookNodes in the notebook."""
		nodes_to_visit = []
		if self.root is not None:
			nodes_to_visit.append(self.root)
		while nodes_to_visit:
			node = nodes_to_visit.pop()
			yield node
			for child in node.get_children(not_deleted=True, unsaved_deleted=True):
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
			notebook_storage,
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
		
		@param notebook_storage: The NotebookStorage to use.
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
		self._notebook_storage = notebook_storage
		self._notebook = notebook
		self._children = []
		self.content_type = content_type
		self.is_deleted = False
		self.parent = parent
		self._title = title
		self.order = order
		self._icon_normal = icon_normal
		self._icon_open = icon_open
		self._title_color_foreground = title_color_foreground
		self._title_color_background = title_color_background
		self._unsaved_changes = set()
		if loaded_from_storage:
			if node_id is None:
				raise IllegalArgumentCombinationError()
			self.node_id = node_id
			self._created_time = created_time
			self._modified_time = modified_time
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
			self._unsaved_changes.add(NotebookNode.NEW)
		
		self.client_preferences = Pref(client_preferences)
		self.client_preferences.change_listeners.add(self._on_client_preferences_change)
	
	def _add_child_node(self, child_node):
		self._children.append(child_node)
		assert child_node.parent is self
		
	def can_add_new_content_child_node(self):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	def can_add_new_folder_child_node(self):
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
		return self.get_children(not_deleted=True, unsaved_deleted=False)
	
	def copy(self, target, with_subtree, behind=None):
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
		if NotebookNode.NEW not in self._unsaved_changes:
			self._unsaved_changes.add(NotebookNode.CHANGED_ICON_NORMAL)
		
		self.modified_time = datetime.now(tz=utc)
	
	@property
	def icon_open(self):
		return self._icon_open
	
	@icon_open.setter
	def icon_open(self, icon_open):
		if self.is_deleted:
			raise IllegalOperationError('Cannot set the open icon of a deleted node')
		
		self._icon_open = icon_open
		if NotebookNode.NEW not in self._unsaved_changes:
			self._unsaved_changes.add(NotebookNode.CHANGED_ICON_OPEN)
		
		self.modified_time = datetime.now(tz=utc)
	
	@property
	def is_dirty(self):
		"""TODO"""
		raise NotImplementedError('TODO')
		
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
	
	def get_children(self, not_deleted=True, unsaved_deleted=False):
		"""TODO"""
		return [child for child in self._children if \
				(not child.is_deleted and not_deleted == True) or \
				(child.is_deleted and unsaved_deleted == True)
				]
	
	def has_children(self):
		"""TODO"""
		return len(self.get_children(not_deleted=True, unsaved_deleted=False)) > 0
	
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
		if NotebookNode.NEW not in self._unsaved_changes:
			self._unsaved_changes.add(NotebookNode.CHANGED_MODIFIED_TIME)
	
	def move(self, target, behind=None):
		"""TODO
		
		Cannot be used to move a node to another workbook. Use copy() for that instead.
		"""
		raise NotImplementedError('TODO')
	
	def new_content_child_node(self, content_type, title, main_payload, additional_payloads, behind=None):
		"""Adds a new child node.
		
		@param content_type: The content type of the node.
		@param title: The title of the node.
		@param main_payload: A tuple consisting of the main paylad name and the main payload data.
		@param additional_payloads: A list containing tuples consisting of paylad names and payload data.
		@param behind: TODO
#		@raise NodeAlreadyExists: If a node with the same id already exists within the notebook.
		"""
		raise NotImplementedError('TODO')
	
	def new_folder_child_node(self, title, behind=None):
		"""Adds a new child node.
		
		@param title: The title of the node.
		@param behind: TODO
#		@raise NodeAlreadyExists: If a node with the same id already exists within the notebook.
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
		
	def save(self):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	@property
	def title(self):
		return self._title
	
	@title.setter
	def title(self, title):
		if self.is_deleted:
			raise IllegalOperationError('Cannot set the title of a deleted node')
		
		self._title = title
		if NotebookNode.NEW not in self._unsaved_changes:
			self._unsaved_changes.add(NotebookNode.CHANGED_TITLE)
		
		self.modified_time = datetime.now(tz=utc)
	
	@property
	def title_color_background(self):
		return self._title_color_background
	
	@title_color_background.setter
	def title_color_background(self, title_color_background):
		if self.is_deleted:
			raise IllegalOperationError('Cannot set the title background color of a deleted node')
		
		self._title_color_background = title_color_background
		if NotebookNode.NEW not in self._unsaved_changes:
			self._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		
		self.modified_time = datetime.now(tz=utc)
	
	@property
	def title_color_foreground(self):
		return self._title_color_foreground
	
	@title_color_foreground.setter
	def title_color_foreground(self, title_color_foreground):
		if self.is_deleted:
			raise IllegalOperationError('Cannot set the title foreground color of a deleted node')
		
		self._title_color_foreground = title_color_foreground
		if NotebookNode.NEW not in self._unsaved_changes:
			self._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		
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
	def can_add_new_content_child_node(self):
		return not self.is_in_trash and not self.is_deleted
	
	def can_add_new_folder_child_node(self):
		return not self.is_in_trash and not self.is_deleted
	
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
		self.is_deleted = True
		if NotebookNode.NEW in self._unsaved_changes:
			self.parent._remove_child_node(self)
			self._unsaved_changes.remove(NotebookNode.NEW)
		else:
			self._unsaved_changes.add(NotebookNode.DELETED)
	
	@property
	def is_dirty(self):
		return len(self._unsaved_changes) != 0 or self.client_preferences.is_dirty()
				
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
		self._unsaved_changes.add(NotebookNode.MOVED)
		
		self.modified_time = datetime.now(tz=utc)
	
	def new_content_child_node(self, content_type, title, main_payload, additional_payloads, behind=None):
		if self.is_in_trash:
			raise IllegalOperationError('Cannot add a child to a node in trash')
		elif self.is_deleted:
			raise IllegalOperationError('Cannot add a child to a deleted node')
			
		child = ContentNode(
				notebook_storage=self._notebook_storage,
				notebook=self._notebook,
				content_type=content_type,
				parent=self,
				title=title,
				loaded_from_storage=False,
				main_payload=main_payload,
				additional_payloads=additional_payloads,
				)
		if behind is None:
			self._add_child_node(child)
		else:
			try:
				i = self._children.index(behind)
				self._children.insert(i + 1, child)
			except ValueError as e:
				raise IllegalOperationError('Unknown child', e)
	
		return child
	
	def new_folder_child_node(self, title, behind=None):
		if self.is_in_trash:
			raise IllegalOperationError('Cannot add a child to a node in trash')
		elif self.is_deleted:
			raise IllegalOperationError('Cannot add a child to a deleted node')
			
		child = FolderNode(
				notebook_storage=self._notebook_storage,
				notebook=self._notebook,
				parent=self,
				title=title,
				loaded_from_storage=False
				)
		if behind is None:
			self._add_child_node(child)
		else:
			try:
				i = self._children.index(behind)
				self._children.insert(i + 1, child)
			except ValueError as e:
				raise IllegalOperationError('Unknown child', e)
		
		return child


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
			notebook_storage,
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
		
		@param notebook_storage: The NotebookStorage to use.
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
				notebook_storage=notebook_storage,
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
	
	@property
	def _notebook_storage_attributes(self):
		"""TODO"""
		attributes = {
				MAIN_PAYLOAD_NAME_ATTRIBUTE.key: self.main_payload_name,
				TITLE_ATTRIBUTE.key: self._title,
				ICON_NORMAL_ATTRIBUTE.key: self._icon_normal,
				ICON_OPEN_ATTRIBUTE.key: self._icon_open,
				CLIENT_PREFERENCES_ATTRIBUTE.key: self.client_preferences._data,
				}
		if self.parent is not None:
			attributes[PARENT_ID_ATTRIBUTE.key] = self.parent.node_id
		if self._created_time is not None:
			attributes[CREATED_TIME_ATTRIBUTE.key] = datetime_to_timestamp(self._created_time)
		if self._modified_time is not None:
			attributes[MODIFIED_TIME_ATTRIBUTE.key] = datetime_to_timestamp(self._modified_time)
		return attributes
	
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
	
	def save(self):
		if self.parent is not None and self.parent.is_dirty:
			if not self.is_deleted or (self.is_deleted and not self.parent.is_deleted):
				raise IllegalOperationError('Cannot save a node if the parent has changes and is not deleted')
		for child in self._children:
			if child.is_deleted and child.is_dirty:
				raise IllegalOperationError('Cannot save a node if it has dirty deleted children')
		
		if NotebookNode.NEW in self._unsaved_changes:
			self._notebook_storage.add_node(
					node_id=self.node_id,
					content_type=self.content_type,
					attributes=self._notebook_storage_attributes,
					payloads=[])
			self._unsaved_changes.remove(NotebookNode.NEW)
			self.client_preferences.reset_dirty()
		elif NotebookNode.DELETED in self._unsaved_changes:
			self._notebook_storage.remove_node(self.node_id)
			self._unsaved_changes.remove(NotebookNode.DELETED)
			self.parent._remove_child_node(self)
		else:
			if NotebookNode.MOVED in self._unsaved_changes or \
					NotebookNode.CHANGED_TITLE in self._unsaved_changes or \
					NotebookNode.CHANGED_ICON_NORMAL in self._unsaved_changes or \
					NotebookNode.CHANGED_ICON_OPEN in self._unsaved_changes or \
					NotebookNode.CHANGED_MODIFIED_TIME in self._unsaved_changes or \
					self.client_preferences.is_dirty():
				self._notebook_storage.set_node_attributes(self.node_id, self._notebook_storage_attributes)
				self._unsaved_changes.discard(NotebookNode.MOVED)
				self._unsaved_changes.discard(NotebookNode.CHANGED_TITLE)
				self._unsaved_changes.discard(NotebookNode.CHANGED_ICON_NORMAL)
				self._unsaved_changes.discard(NotebookNode.CHANGED_ICON_OPEN)
				self._unsaved_changes.discard(NotebookNode.CHANGED_MODIFIED_TIME)
				self.client_preferences.reset_dirty()
			if ContentNode.PAYLOAD_CHANGE in self._unsaved_changes:
				for payload_name in list(self._payload_names_to_remove):
					self._notebook_storage.remove_node_payload(self.node_id, payload_name)
					self._payload_names_to_remove.remove(payload_name)
				self._unsaved_changes.remove(ContentNode.PAYLOAD_CHANGE)
	
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
			notebook_storage,
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
		
		@param notebook_storage: The NotebookStorage to use.
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
				notebook_storage=notebook_storage,
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
	
	@property
	def _notebook_storage_attributes(self):
		"""TODO"""
		attributes = {
				TITLE_ATTRIBUTE.key: self._title,
				ICON_NORMAL_ATTRIBUTE.key: self._icon_normal,
				ICON_OPEN_ATTRIBUTE.key: self._icon_open,
				CLIENT_PREFERENCES_ATTRIBUTE.key: self.client_preferences._data,
				}
		if self.parent is not None:
			attributes[PARENT_ID_ATTRIBUTE.key] = self.parent.node_id
		if self._created_time is not None:
			attributes[CREATED_TIME_ATTRIBUTE.key] = datetime_to_timestamp(self._created_time)
		if self._modified_time is not None:
			attributes[MODIFIED_TIME_ATTRIBUTE.key] = datetime_to_timestamp(self._modified_time)
		return attributes
	
	def save(self):
		if self.parent is not None and self.parent.is_dirty:
			if not self.is_deleted or (self.is_deleted and not self.parent.is_deleted):
				raise IllegalOperationError('Cannot save a node if the parent has changes and is not deleted')
		for child in self._children:
			if child.is_deleted and child.is_dirty:
				raise IllegalOperationError('Cannot save a node if it has dirty deleted children')
		
		if NotebookNode.NEW in self._unsaved_changes:
			self._notebook_storage.add_node(
					node_id=self.node_id,
					content_type=self.content_type,
					attributes=self._notebook_storage_attributes,
					payloads=[])
			self._unsaved_changes.remove(NotebookNode.NEW)
			self.client_preferences.reset_dirty()
		elif NotebookNode.DELETED in self._unsaved_changes:
			self._notebook_storage.remove_node(self.node_id)
			self._unsaved_changes.remove(NotebookNode.DELETED)
			self.parent._remove_child_node(self)
		else:
			if NotebookNode.MOVED in self._unsaved_changes or \
					NotebookNode.CHANGED_TITLE in self._unsaved_changes or \
					NotebookNode.CHANGED_ICON_NORMAL in self._unsaved_changes or \
					NotebookNode.CHANGED_ICON_OPEN in self._unsaved_changes or \
					NotebookNode.CHANGED_MODIFIED_TIME in self._unsaved_changes or \
					self.client_preferences.is_dirty():
				self._notebook_storage.set_node_attributes(self.node_id, self._notebook_storage_attributes)
				self._unsaved_changes.discard(NotebookNode.MOVED)
				self._unsaved_changes.discard(NotebookNode.CHANGED_TITLE)
				self._unsaved_changes.discard(NotebookNode.CHANGED_ICON_NORMAL)
				self._unsaved_changes.discard(NotebookNode.CHANGED_ICON_OPEN)
				self._unsaved_changes.discard(NotebookNode.CHANGED_MODIFIED_TIME)
				self.client_preferences.reset_dirty()
	
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
			notebook_storage,
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
		
		@param notebook_storage: The NotebookStorage to use.
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
				notebook_storage=notebook_storage,
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

	def can_add_new_content_child_node(self):
		return False
	
	def can_add_new_folder_child_node(self):
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
	
	def delete(self):
		raise IllegalOperationError('Cannot delete the trash node')
	
	@property
	def is_dirty(self):
		return len(self._unsaved_changes) != 0 or self.client_preferences.is_dirty()
				
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
	
	def new_content_child_node(self, content_type, title, main_payload, additional_payloads, behind=None):
		raise IllegalOperationError('Cannot add a child to the trash')
	
	def new_folder_child_node(self, title, behind=None):
		raise IllegalOperationError('Cannot add a child to the trash')
	
	@property
	def _notebook_storage_attributes(self):
		"""TODO"""
		attributes = {
				TITLE_ATTRIBUTE.key: self._title,
				ICON_NORMAL_ATTRIBUTE.key: self._icon_normal,
				ICON_OPEN_ATTRIBUTE.key: self._icon_open,
				CLIENT_PREFERENCES_ATTRIBUTE.key: self.client_preferences._data,
				}
		if self.parent is not None:
			attributes[PARENT_ID_ATTRIBUTE.key] = self.parent.node_id
		if self._created_time is not None:
			attributes[CREATED_TIME_ATTRIBUTE.key] = datetime_to_timestamp(self._created_time)
		if self._modified_time is not None:
			attributes[MODIFIED_TIME_ATTRIBUTE.key] = datetime_to_timestamp(self._modified_time)
		return attributes
	
	def save(self):
		if self.parent is not None and self.parent.is_dirty:
			if not self.is_deleted or (self.is_deleted and not self.parent.is_deleted):
				raise IllegalOperationError('Cannot save a node if the parent has changes and is not deleted')
		for child in self._children:
			if child.is_deleted and child.is_dirty:
				raise IllegalOperationError('Cannot save a node if it has dirty deleted children')
		
		if NotebookNode.NEW in self._unsaved_changes:
			self._notebook_storage.add_node(
					node_id=self.node_id,
					content_type=self.content_type,
					attributes=self._notebook_storage_attributes,
					payloads=[])
			self._unsaved_changes.remove(NotebookNode.NEW)
			self.client_preferences.reset_dirty()
		else:
			if NotebookNode.CHANGED_TITLE in self._unsaved_changes or \
					NotebookNode.CHANGED_ICON_NORMAL in self._unsaved_changes or \
					NotebookNode.CHANGED_ICON_OPEN in self._unsaved_changes or \
					NotebookNode.CHANGED_MODIFIED_TIME in self._unsaved_changes or \
					self.client_preferences.is_dirty():
				self._notebook_storage.set_node_attributes(self.node_id, self._notebook_storage_attributes)
				self._unsaved_changes.discard(NotebookNode.CHANGED_TITLE)
				self._unsaved_changes.discard(NotebookNode.CHANGED_ICON_NORMAL)
				self._unsaved_changes.discard(NotebookNode.CHANGED_ICON_OPEN)
				self._unsaved_changes.discard(NotebookNode.CHANGED_MODIFIED_TIME)
				self.client_preferences.reset_dirty()
	
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

from collections import OrderedDict
import io
import os
import uuid

from keepnote.pref import Pref
from keepnote.notebooknew.storage import StoredNode

__all__ = [
		'Notebook',
		'NotebookNode',
		'ContentNode',
		'FolderNode',
		'TrashNode',
		'NotebookError',
		'IllegalArgumentCombinationError',
		'IllegalOperationError',
		'InvalidStructureError',
		'PayloadAlreadyExistsError',
		'PayloadDoesNotExistError'
		]

# Content types
CONTENT_TYPE_HTML = u"text/html"
CONTENT_TYPE_TRASH = u"application/x-notebook-trash"
CONTENT_TYPE_FOLDER = u"application/x-notebook-dir"
#CONTENT_TYPE_UNKNOWN = u"application/x-notebook-unknown"

# Attribute names
PARENT_ID_ATTRIBUTE = 'parent_id'
TITLE_ATTRIBUTE = 'title'
MAIN_PAYLOAD_NAME_ATTRIBUTE = 'main_payload_name'

def new_node_id():
	"""Generate a new, random node id."""
	return unicode(uuid.uuid4())

class Notebook(object):
	"""A collection of nodes.
	
	@ivar root: The root NotebookNode.
	@ivar trash: TODO
	@ivar client_preferences: A Pref containing the notebook's client preferences.
	@ivar is_dirty: TODO
	"""
	
	def __init__(self, notebook_storage):
		"""Constructor.
		
		@param notebook_storage: The NotebookStorage to use. 
		"""
		self._notebook_storage = notebook_storage
		self.root = None
		self.trash = None
		self.client_preferences = Pref()
		self.is_dirty = False
		
		self._init_from_storage()
		
	def _init_from_storage(self):
		"""Initializes the Notebook from the NotebookStorage."""

		# Load all StoredNodes.		
		stored_nodes = list(self._notebook_storage.get_all_nodes())
		
		# If no nodes exist, create a single root node.
		if stored_nodes == []:
			node_id = new_node_id()
			self._notebook_storage.add_node(node_id=node_id, content_type=CONTENT_TYPE_FOLDER, attributes={}, payloads=[])
			# TODO: Enable this line (a test will fail)
			#stored_nodes = self._notebook_storage.get_all_nodes()
			stored_nodes.append(StoredNode(node_id=node_id, content_type=CONTENT_TYPE_FOLDER, attributes={}, payload_names=[]))
		
		# Create NotebookNodes for all StoredNotes and index all StoredNotes and NotebookNodes by id.
		nodes_by_id = {}
		for stored_node in stored_nodes:
			title = stored_node.attributes[TITLE_ATTRIBUTE] if TITLE_ATTRIBUTE in stored_node.attributes else ''
			if stored_node.content_type == CONTENT_TYPE_FOLDER:
				notebook_node = FolderNode(
						notebook_storage=self._notebook_storage,
						notebook=self,
						node_id=stored_node.node_id,
						parent=None,
						title=title,
						loaded_from_storage=True
						)
			elif stored_node.content_type == CONTENT_TYPE_TRASH:
				notebook_node = TrashNode(
						notebook_storage=self._notebook_storage,
						notebook=self,
						node_id=stored_node.node_id,
						parent=None,
						title=title,
						loaded_from_storage=True
						)
			else:
				main_payload_name = stored_node.attributes[MAIN_PAYLOAD_NAME_ATTRIBUTE]
				additional_payload_names = [payload_name for payload_name in stored_node.payload_names if payload_name != main_payload_name]
				notebook_node = ContentNode(
						notebook_storage=self._notebook_storage,
						notebook=self,
						node_id=stored_node.node_id,
						content_type=stored_node.content_type,
						parent=None,
						title=title,
						loaded_from_storage=True,
						main_payload_name=main_payload_name,
						additional_payload_names=additional_payload_names,
						)
			nodes_by_id[stored_node.node_id] = (stored_node, notebook_node)
		
		# Create the NotebookNode tree structure.
		for stored_node, notebook_node in nodes_by_id.values():
			if PARENT_ID_ATTRIBUTE in stored_node.attributes:
				parent_id = stored_node.attributes[PARENT_ID_ATTRIBUTE]
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
				parent_notebook_node.children.append(notebook_node)
			else:
				if self.root is not None:
					raise InvalidStructureError('Multiple root nodes found')
				self.root = notebook_node
			if notebook_node.content_type == CONTENT_TYPE_TRASH:
				self.trash = notebook_node
		if self.root is None:
			raise InvalidStructureError('No root node found')
			
		# If no trash node exists, create it.
		if self.trash is None:
			node_id = new_node_id()
			self._notebook_storage.add_node(node_id=node_id, content_type=CONTENT_TYPE_TRASH, attributes={ PARENT_ID_ATTRIBUTE: self.root.node_id }, payloads=[])
			notebook_node = TrashNode(
					notebook_storage=self._notebook_storage,
					notebook=self,
					node_id=node_id,
					parent=self.root,
					title='', # TODO
					loaded_from_storage=True
					)
			self.trash = notebook_node
		
		if self.trash.parent is not self.root:
			raise InvalidStructureError('The trash node is not a direct child of the root node')
		
		# Sort children by their id.
		for stored_node, notebook_node in nodes_by_id.values():
			notebook_node.children.sort(key=lambda child_notebook_node: child_notebook_node.node_id)
	
	def save(self):
		"""Saves all changes to the notebook."""
		pass
	
	def _traverse_tree(self):
		"""A generator method that yields all NotebookNodes in the notebook."""
		pass
		

class NotebookNode(object):
	"""A node in a notebook. Every node has an identifier, a content type and a title.
	
	@ivar node_id: The id of the node.
	@ivar children: The node's children.
	@ivar content_type: The content type of the node.
	@ivar parent: The parent of the node.
	@ivar title: The title of the node.
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
	MOVED = StorageChange('MOVED')

	def __init__(self, notebook_storage, notebook, node_id, content_type, parent, title, loaded_from_storage):
		"""Constructor.
		
		@param notebook_storage: The NotebookStorage to use.
		@param notebook: The notebook the node is in.
		@param node_id: The id of the new node.
		@param content_type: The content type of node.
		@param parent: The parent of the node or None.
		@param title: The title of the node.
		@param loaded_from_storage: TODO
		"""
		self._notebook_storage = notebook_storage
		self._notebook = notebook
		self.node_id = node_id
		self.children = []
		self.content_type = content_type
		self.is_deleted = False
		self.parent = parent
		self._title = title
		self._unsaved_changes = []
		if not loaded_from_storage:
			self._unsaved_changes.append(NotebookNode.NEW)
	
	def can_add_new_content_child_node(self):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	def can_add_new_folder_child_node(self):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	def can_copy(self, target, with_subtree):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	def can_move(self, target):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	def copy(self, target, with_subtree, behind=None):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	def delete(self):
		"""TODO"""
		raise NotImplementedError('TODO')
	
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
	
	def move(self, target, behind=None):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	def new_content_child_node(self, node_id, content_type, title, main_payload, additional_payloads, behind=None):
		"""Adds a new child node.
		
		@param node_id: The id of the new node. Must be unique within the notebook.
		@param content_type: The content type of the node.
		@param title: The title of the node.
		@param main_payload: A tuple consisting of the main paylad name and the main payload data.
		@param additional_payloads: A list containing tuples consisting of paylad names and payload data.
		@param behind: TODO
#		@raise NodeAlreadyExists: If a node with the same id already exists within the notebook.
		"""
		raise NotImplementedError('TODO')
	
	def new_folder_child_node(self, node_id, title, behind=None):
		"""Adds a new child node.
		
		@param node_id: The id of the new node. Must be unique within the notebook.
		@param title: The title of the node.
		@param behind: TODO
#		@raise NodeAlreadyExists: If a node with the same id already exists within the notebook.
		"""
		raise NotImplementedError('TODO')
	
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
			self._unsaved_changes.append(NotebookNode.CHANGED_TITLE)


class ContentNode(NotebookNode):
	"""A node with content in a notebook. Every content node has at least one payload and may have additional payloads.

	TODO:
	@ivar main_payload_name
	@ivar additional_payload_names: The names of the payloads of the node.
	"""
	
	# Change constants
	PAYLOAD_CHANGE = NotebookNode.StorageChange('PAYLOAD_CHANGE')
	
	# TODO: Use classmethods for loading from storage / for creating new in memory

	def __init__(self, notebook_storage, notebook, node_id, content_type, parent, title, loaded_from_storage=None, 
			main_payload=None, additional_payloads=None, main_payload_name=None, additional_payload_names=None,
			is_dirty=None):
		"""Constructor.
		
		Either main_payload and additional_payloads or main_payload_name and additional_payload_names must be passed.
		
		@param notebook_storage: The NotebookStorage to use.
		@param notebook: The notebook the node is in.
		@param node_id: The id of the new node.
		@param content_type: The content type of node.
		@param parent: The parent of the node or None.
		@param title: The title of the node.
		@param loaded_from_storage: TODO
		@param main_payload: A tuple consisting of the main paylad name and the main payload data.
		@param additional_payloads: A list containing tuples consisting of paylad names and payload data.
		@param main_payload_name: The name of the main payload.
		@param additional_payload_names: The names of the additional payloads.
		@param is_dirty: Indicates whether the node has changed since it was last saved.
		"""
		super(ContentNode, self).__init__(
				notebook_storage=notebook_storage,
				notebook=notebook,
				node_id=node_id,
				content_type=content_type,
				parent=parent,
				title=title,
				loaded_from_storage=loaded_from_storage,
				)
		if loaded_from_storage and (main_payload_name is None or additional_payload_names is None):
			raise IllegalArgumentCombinationError()
		elif not loaded_from_storage and (main_payload is None or additional_payloads is None):
			raise IllegalArgumentCombinationError()
		
		if main_payload_name is not None:
			self.main_payload_name = main_payload_name
			self.additional_payload_names = additional_payload_names
			self._payloads_to_store = OrderedDict()
		else:
			self.main_payload_name = main_payload[0]
			self.additional_payload_names = [additional_payload[0] for additional_payload in additional_payloads]
			self._payloads_to_store = OrderedDict([main_payload] + additional_payloads)
		self._payload_names_to_remove = []
	
	def add_additional_payload(self, payload_name, payload_data):
		"""TODO"""
		if payload_name == self.main_payload_name:
			raise PayloadAlreadyExistsError('A payload with the name "{name}" already exists'.format(name=payload_name))
		elif payload_name in self.additional_payload_names:
			raise PayloadAlreadyExistsError('A payload with the name "{name}" already exists'.format(name=payload_name))
		
		self.additional_payload_names.append(payload_name)
		self._payloads_to_store[payload_name] = payload_data
		if NotebookNode.NEW not in self._unsaved_changes and ContentNode.PAYLOAD_CHANGE not in self._unsaved_changes:
			self._unsaved_changes.append(ContentNode.PAYLOAD_CHANGE)
	
	def can_add_new_content_child_node(self):
		"""TODO"""
		return not self.is_in_trash and not self.is_deleted
	
	def can_add_new_folder_child_node(self):
		"""TODO"""
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
	
	def can_move(self, target):
		return \
				not self.is_deleted and \
				self._notebook == target._notebook and \
				not self.is_root and \
				not self.is_node_a_child(target)
	
	def copy(self, target, with_subtree, behind=None):
		"""TODO"""
		if self.is_deleted:
			raise IllegalOperationError('Cannot copy a deleted node')
		elif target.is_trash or target.is_in_trash:
			raise IllegalOperationError('Cannot copy a node to the trash')
		elif with_subtree and self.is_node_a_child(target):
			raise IllegalOperationError('Cannot copy a node with its children to a child')
		
		copy = target.new_content_child_node(
				node_id=new_node_id(),
				content_type=self.content_type,
				title=self._title,
				main_payload=(self.main_payload_name, self.get_payload(self.main_payload_name)),
				additional_payloads=[(additional_payload_name, self.get_payload(additional_payload_name)) for additional_payload_name in self.additional_payload_names],
				behind=behind
				)
		if with_subtree:
			for child in self.children:
				child.copy(copy, with_subtree=with_subtree)
		
		return copy
	
	def delete(self):
		"""TODO"""
		if self.parent is None:
			raise IllegalOperationError('Cannot delete the root node')
		for child in self.children:
			child.delete()
		self.parent.children.remove(self)
		self.is_deleted = True
		if NotebookNode.NEW in self._unsaved_changes:
			self._unsaved_changes.remove(NotebookNode.NEW)
		else:
			self._unsaved_changes.append(NotebookNode.DELETED)
	
	def get_payload(self, payload_name):
		"""TODO"""
		if payload_name in self._payloads_to_store:
			return self._payloads_to_store[payload_name]
		elif payload_name == self.main_payload_name or payload_name in self.additional_payload_names:
			return self._notebook_storage.get_node_payload(self.node_id, payload_name).read()
		else:
			raise PayloadDoesNotExistError(payload_name)
	
	@property
	def is_dirty(self):
		return len(self._unsaved_changes) != 0
				
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
			target.children.append(self)
		else:
			try:
				i = target.children.index(behind)
				target.children.insert(i + 1, self)
			except ValueError as e:
				raise IllegalOperationError('Unknown child', e)
		self.parent.children.remove(self)
		self.parent = target
		self._unsaved_changes.append(NotebookNode.MOVED)
	
	def new_content_child_node(self, node_id, content_type, title, main_payload, additional_payloads, behind=None):
#		if additional_payloads is None:
#			additional_payloads = []
		
		if self.is_in_trash:
			raise IllegalOperationError('Cannot add a child to a node in trash')
		elif self.is_deleted:
			raise IllegalOperationError('Cannot add a child to a deleted node')
			
		child = ContentNode(
				notebook_storage=self._notebook_storage,
				notebook=self._notebook,
				node_id=node_id,
				content_type=content_type,
				parent=self,
				title=title,
				loaded_from_storage=False,
				main_payload=main_payload,
				additional_payloads=additional_payloads
				)
		if behind is None:
			self.children.append(child)
		else:
			try:
				i = self.children.index(behind)
				self.children.insert(i + 1, child)
			except ValueError as e:
				raise IllegalOperationError('Unknown child', e)
	
		return child
	
	def new_folder_child_node(self, node_id, title, behind=None):
		if self.is_in_trash:
			raise IllegalOperationError('Cannot add a child to a node in trash')
		elif self.is_deleted:
			raise IllegalOperationError('Cannot add a child to a deleted node')
			
		child = FolderNode(
				notebook_storage=self._notebook_storage,
				notebook=self._notebook,
				node_id=node_id,
				parent=self,
				title=title,
				loaded_from_storage=False
				)
		if behind is None:
			self.children.append(child)
		else:
			try:
				i = self.children.index(behind)
				self.children.insert(i + 1, child)
			except ValueError as e:
				raise IllegalOperationError('Unknown child', e)
		
		return child
	
	@property
	def _notebook_storage_attributes(self):
		"""TODO"""
		attributes = {
				TITLE_ATTRIBUTE: self._title,
				MAIN_PAYLOAD_NAME_ATTRIBUTE: self.main_payload_name
				}
		if self.parent is not None:
			attributes[PARENT_ID_ATTRIBUTE] = self.parent.node_id
		return attributes
	
	def remove_additional_payload(self, payload_name):
		"""TODO"""
		self.additional_payload_names.remove(payload_name)
		if payload_name in self._payloads_to_store:
			del self._payloads_to_store[payload_name]
		else:
			self._payload_names_to_remove.append(payload_name)
			self._unsaved_changes.append(ContentNode.PAYLOAD_CHANGE)
	
	def save(self):
#		if not self.is_dirty:
#			return
		if self.parent is not None and self.parent.is_dirty:
			raise IllegalOperationError('Cannot save a node if the parent has changes')
		for child in self.children:
			if child.is_deleted and child.is_dirty:
				raise IllegalOperationError('Cannot save a node if it has dirty deleted children')
		
		if NotebookNode.NEW in self._unsaved_changes:
			self._notebook_storage.add_node(
					node_id=self.node_id,
					content_type=self.content_type,
					attributes=self._notebook_storage_attributes,
					payloads=[(payload_name, io.BytesIO(payload_data)) for (payload_name, payload_data) in self._payloads_to_store.iteritems()])
			self._payloads_to_store.clear()
			self._unsaved_changes.remove(NotebookNode.NEW)
		elif NotebookNode.DELETED in self._unsaved_changes:
			self._notebook_storage.remove_node(self.node_id)
			self._unsaved_changes.remove(NotebookNode.DELETED)
		elif NotebookNode.CHANGED_TITLE in self._unsaved_changes:
			self._notebook_storage.set_node_attributes(self._notebook_storage_attributes)
			self._unsaved_changes.remove(NotebookNode.CHANGED_TITLE)
		elif ContentNode.PAYLOAD_CHANGE in self._unsaved_changes:
			for payload_name, payload_data in self._payloads_to_store.items():
				self._notebook_storage.add_node_payload(self.node_id, payload_name, io.BytesIO(payload_data))
				del self._payloads_to_store[payload_name]
			for payload_name in list(self._payload_names_to_remove):
				self._notebook_storage.remove_node_payload(self.node_id, payload_name)
				self._payload_names_to_remove.remove(payload_name)
			self._unsaved_changes.remove(ContentNode.PAYLOAD_CHANGE)
	
	def set_main_payload(self, payload_data):
		"""TODO"""
		self._payloads_to_store[self.main_payload_name] = payload_data
		if self.main_payload_name not in self._payload_names_to_remove:
			self._payload_names_to_remove.append(self.main_payload_name)
		if NotebookNode.NEW not in self._unsaved_changes and ContentNode.PAYLOAD_CHANGE not in self._unsaved_changes:
			self._unsaved_changes.append(ContentNode.PAYLOAD_CHANGE)

	def __repr__(self):
		return '{cls}[{node_id}, {content_type}, {title}]'.format(
				cls=self.__class__.__name__,
				dirty='*' if self.is_dirty else '-',
				**self.__dict__
				)


class FolderNode(NotebookNode):
	"""A folder node in a notebook. A folder node has no content.
	"""

	def __init__(self, notebook_storage, notebook, node_id, parent, title, loaded_from_storage):
		"""Constructor.
		
		@param notebook_storage: The NotebookStorage to use.
		@param notebook: The notebook the node is in.
		@param node_id: The id of the new node.
		@param parent: The parent of the node or None.
		@param title: The title of the node.
		@param loaded_from_storage: TODO
		"""
		super(FolderNode, self).__init__(
				notebook_storage=notebook_storage,
				notebook=notebook,
				node_id=node_id,
				content_type=CONTENT_TYPE_FOLDER,
				parent=parent,
				title=title,
				loaded_from_storage=loaded_from_storage
				)
	
	@property
	def is_dirty(self):
		return len(self._unsaved_changes) != 0

	def __repr__(self):
		return '{cls}[{node_id}, {title}]'.format(
				cls=self.__class__.__name__,
				dirty='*' if self.is_dirty else '-',
				**self.__dict__
				)

class TrashNode(FolderNode):
	"""A trash node in a notebook. A trash node has no content.
	"""

	def __init__(self, notebook_storage, notebook, node_id, parent, title, loaded_from_storage):
		"""Constructor.
		
		@param notebook_storage: The NotebookStorage to use.
		@param notebook: The notebook the node is in.
		@param node_id: The id of the new node.
		@param parent: The parent of the node or None.
		@param title: The title of the node.
		@param loaded_from_storage: TODO
		"""
		super(FolderNode, self).__init__(
				notebook_storage=notebook_storage,
				notebook=notebook,
				node_id=node_id,
				content_type=CONTENT_TYPE_TRASH,
				parent=parent,
				title=title,
				loaded_from_storage=loaded_from_storage,
				)

	@property
	def is_dirty(self):
		return len(self._unsaved_changes) != 0

	def __repr__(self):
		return '{cls}[{node_id}, {title}]'.format(
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


class PayloadAlreadyExistsError(NotebookError):
	pass


class PayloadDoesNotExistError(NotebookError):
	pass

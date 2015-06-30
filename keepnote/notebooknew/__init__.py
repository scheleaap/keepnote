import os
import uuid

from collections import OrderedDict
from keepnote.pref import Pref
from keepnote.notebooknew.storage import StoredNode

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
						node_id=stored_node.node_id,
						parent=None,
						title=title,
						is_dirty=False,
						)
			elif stored_node.content_type == CONTENT_TYPE_TRASH:
				notebook_node = TrashNode(
						notebook_storage=self._notebook_storage,
						node_id=stored_node.node_id,
						parent=None,
						title=title,
						is_dirty=False,
						)
			else:
				main_payload_name = stored_node.attributes[MAIN_PAYLOAD_NAME_ATTRIBUTE]
				additional_payload_names = [payload_name for payload_name in stored_node.payload_names if payload_name != main_payload_name]
				notebook_node = ContentNode(
						notebook_storage=self._notebook_storage,
						node_id=stored_node.node_id,
						content_type=stored_node.content_type,
						parent=None,
						title=title,
						main_payload_name=main_payload_name,
						additional_payload_names=additional_payload_names,
						is_dirty=False,
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
					node_id=node_id,
					parent=self.root,
					title='', # TODO
					is_dirty=False,
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
	@ivar is_deleted_unsaved: Indicates whether the node has been deleted from the notebook but not deleted from storage yet. 
	"""

	def __init__(self, notebook_storage, node_id, content_type, parent, title, is_dirty=True):
		"""Constructor.
		
		@param notebook_storage: The NotebookStorage to use. 
		@param node_id: The id of the new node.
		@param content_type: The content type of node.
		@param is_dirty: Indicates whether the node has changed since it was last saved.
		@param parent: The parent of the node or None.
		@param title: The title of the node.
		"""
		self._notebook_storage = notebook_storage
		self.node_id = node_id
		self.children = []
		self.content_type = content_type
		self.is_deleted_unsaved = False
		self.is_dirty = is_dirty
		self.parent = parent
		self.title = title
	
	def can_add_new_content_child_node(self):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	def can_add_new_folder_child_node(self):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	def can_copy(self, target, with_subtree):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	def copy(self, target, with_subtree):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	def delete(self):
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
	
	def new_content_child_node(self, node_id, content_type, title, main_payload, additional_payloads, after=None):
		"""Adds a new child node.
		
		@param node_id: The id of the new node. Must be unique within the notebook.
		@param content_type: The content type of the node.
		@param title: The title of the node.
		@param main_payload: A tuple consisting of the main paylad name and the main payload data.
		@param additional_payloads: A list containing tuples consisting of paylad names and payload data.
		@param after: TODO
#		@raise NodeAlreadyExists: If a node with the same id already exists within the notebook.
		"""
		raise NotImplementedError('TODO')
	
	def new_folder_child_node(self, node_id, title, after=None):
		"""Adds a new child node.
		
		@param node_id: The id of the new node. Must be unique within the notebook.
		@param title: The title of the node.
		@param after: TODO
#		@raise NodeAlreadyExists: If a node with the same id already exists within the notebook.
		"""


class ContentNode(NotebookNode):
	"""A node with content in a notebook. Every content node has at least one payload and may have additional payloads.

	TODO:
	@ivar main_payload_name
	@ivar additional_payload_names: The names of the payloads of the node.
	"""
	
	# TODO: Use classmethods for loading from storage / for creating new in memory

	def __init__(self, notebook_storage, node_id, content_type, parent, title, is_dirty, main_payload=None, additional_payloads=None, main_payload_name=None, additional_payload_names=None):
		"""Constructor.
		
		Either main_payload and additional_payloads or main_payload_name and additional_payload_names must be passed.
		
		@param notebook_storage: The NotebookStorage to use. 
		@param node_id: The id of the new node.
		@param content_type: The content type of node.
		@param parent: The parent of the node or None.
		@param title: The title of the node.
		@param main_payload: A tuple consisting of the main paylad name and the main payload data.
		@param additional_payloads: A list containing tuples consisting of paylad names and payload data.
		@param main_payload_name: The name of the main payload.
		@param additional_payload_names: The names of the additional payloads.
		@param is_dirty: Indicates whether the node has changed since it was last saved.
		"""
		super(ContentNode, self).__init__(
				notebook_storage=notebook_storage,
				node_id=node_id,
				content_type=content_type,
				parent=parent,
				title=title,
				is_dirty=is_dirty,
				)
		if main_payload_name is not None:
			self.main_payload_name = main_payload_name
			self.additional_payload_names = additional_payload_names
			self.payloads = OrderedDict()
		else:
			self.main_payload_name = main_payload[0]
			self.additional_payload_names = [additional_payload[0] for additional_payload in additional_payloads]
			self.payloads = OrderedDict([main_payload] + additional_payloads)
	
	def add_additional_payload(self, payload_name, payload_data):
		"""TODO"""
		if payload_name == self.main_payload_name:
			raise PayloadAlreadyExistsError('A payload with the name "{name}" already exists'.format(name=payload_name))
		if payload_name in self.additional_payload_names:
			raise PayloadAlreadyExistsError('A payload with the name "{name}" already exists'.format(name=payload_name))
		
		self.additional_payload_names.append(payload_name)
		self.payloads[payload_name] = payload_data
		
	def can_add_new_content_child_node(self):
		"""TODO"""
		return not self.is_in_trash and not self.is_deleted_unsaved
	
	def can_add_new_folder_child_node(self):
		"""TODO"""
		return not self.is_in_trash and not self.is_deleted_unsaved
	
	def can_copy(self, target, with_subtree):
		return True
	
	def copy(self, target, with_subtree):
		"""TODO"""
		target.new_content_child_node(
				node_id=new_node_id(),
				content_type=self.content_type,
				title=self.title,
				main_payload=(self.main_payload_name, self.get_payload(self.main_payload_name)),
				additional_payloads=[(additional_payload_name, self.get_payload(additional_payload_name)) for additional_payload_name in self.additional_payload_names]
				)
	
	def delete(self):
		"""TODO"""
		if self.parent is None:
			raise IllegalOperationError('Cannot delete the root node')
		for child in self.children:
			child.delete()
		self.parent.children.remove(self)
		self.is_deleted_unsaved = True
		self.is_dirty = True
	
	def get_payload(self, payload_name):
		"""TODO"""
		if payload_name in self.payloads:
			return self.payloads[payload_name]
		elif payload_name == self.main_payload_name or payload_name in self.additional_payload_names:
			return self._notebook_storage.get_node_payload(self.node_id, payload_name).read()
		else:
			raise PayloadDoesNotExistError(payload_name)
		
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
	
	def new_content_child_node(self, node_id, content_type, title, main_payload, additional_payloads, after=None):
#		if additional_payloads is None:
#			additional_payloads = []
		
		if self.is_in_trash:
			raise IllegalOperationError('Cannot add a child to a node in trash')
		elif self.is_deleted_unsaved:
			raise IllegalOperationError('Cannot add a child to a deleted node')
			
		child = ContentNode(
				notebook_storage=self._notebook_storage,
				node_id=node_id,
				content_type=content_type,
				parent=self,
				title=title,
				main_payload=main_payload,
				additional_payloads=additional_payloads,
				is_dirty=True,
				)
		self.children.append(child)
		
		return child
	
	def new_folder_child_node(self, node_id, title, after=None):
		if self.is_in_trash:
			raise IllegalOperationError('Cannot add a child to a node in trash')
		elif self.is_deleted_unsaved:
			raise IllegalOperationError('Cannot add a child to a deleted node')
			
		child = FolderNode(
				notebook_storage=self._notebook_storage,
				node_id=node_id,
				parent=self,
				title=title,
				is_dirty=True)
		self.children.append(child)
		
		return child
	
	def remove_additional_payload(self, payload_name):
		"""TODO"""
		self.additional_payload_names.remove(payload_name)
		if payload_name in self.payloads:
			del self.payloads[payload_name]
	
	def set_main_payload(self, payload_data):
		"""TODO"""
		self.payloads[self.main_payload_name] = payload_data


class FolderNode(NotebookNode):
	"""A folder node in a notebook. A folder node has no content.
	"""

	def __init__(self, notebook_storage, node_id, parent, title, is_dirty):
		"""Constructor.
		
		@param notebook_storage: The NotebookStorage to use. 
		@param node_id: The id of the new node.
		@param parent: The parent of the node or None.
		@param title: The title of the node.
		@param is_dirty: Indicates whether the node has changed since it was last saved.
		"""
		super(FolderNode, self).__init__(
				notebook_storage=notebook_storage,
				node_id=node_id,
				content_type=CONTENT_TYPE_FOLDER,
				parent=parent,
				title=title,
				is_dirty=is_dirty,
				)

class TrashNode(FolderNode):
	"""A trash node in a notebook. A trash node has no content.
	"""

	def __init__(self, notebook_storage, node_id, parent, title, is_dirty):
		"""Constructor.
		
		@param notebook_storage: The NotebookStorage to use. 
		@param node_id: The id of the new node.
		@param parent: The parent of the node or None.
		@param title: The title of the node.
		@param is_dirty: Indicates whether the node has changed since it was last saved.
		"""
		super(FolderNode, self).__init__(
				notebook_storage=notebook_storage,
				node_id=node_id,
				content_type=CONTENT_TYPE_TRASH,
				parent=parent,
				title=title,
				is_dirty=is_dirty,
				)
	

class NotebookError(Exception):
	pass


class IllegalOperationError(NotebookError):
	pass

class InvalidStructureError(NotebookError):
	pass


class PayloadAlreadyExistsError(NotebookError):
	pass


class PayloadDoesNotExistError(NotebookError):
	pass

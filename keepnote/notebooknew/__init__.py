import os
import uuid

from collections import OrderedDict
from keepnote.pref import Pref
from keepnote.notebooknew.storage import StoredNode

# Content types
CONTENT_TYPE_HTML = u"text/html"
#CONTENT_TYPE_TRASH = u"application/x-notebook-trash"
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
	@ivar client_preferences: A Pref containing the notebook's client preferences.
	"""
	
	def __init__(self, notebook_storage):
		"""Constructor.
		
		@param notebook_storage: The NotebookStorage to use. 
		"""
		self._notebook_storage = notebook_storage
		self.root = None
		self.client_preferences = Pref()
		
		self._init_from_storage()
	
		
	def _init_from_storage(self):
		"""Initializes the Notebook from the NotebookStorage."""

		# Load all StoredNodes.		
		stored_nodes = list(self._notebook_storage.get_all_nodes())
		
		# If no nodes exist, create a single root node.
		if stored_nodes == []:
			node_id = _new_node_id()
			self._notebook_storage.add_node(node_id=node_id, content_type=CONTENT_TYPE_FOLDER, attributes={}, payloads=[])
			# TODO: Enable this line (a test will fail)
			#stored_nodes = self._notebook_storage.get_all_nodes()
			stored_nodes.append(StoredNode(node_id=node_id, content_type=CONTENT_TYPE_FOLDER, attributes={}, payload_names=[]))
		
		# Create NotebookNodes for all StoredNotes and index all StoredNotes and NotebookNodes by id.
		nodes_by_id = {}
		for stored_node in stored_nodes:
			title = stored_node.attributes[TITLE_ATTRIBUTE] if TITLE_ATTRIBUTE in stored_node.attributes else ''
			notebook_node = NotebookNode(
					node_id=stored_node.node_id,
					content_type=stored_node.content_type,
					parent=None,
					payload_names=stored_node.payload_names,
					title=title,
					is_dirty=False
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
		if self.root is None:
			raise InvalidStructureError('No root node found')
		
		# Sort children by their id.
		for stored_node, notebook_node in nodes_by_id.values():
			notebook_node.children.sort(key=lambda child_notebook_node: child_notebook_node.node_id)
	
	def save(self):
		"""Saves all changes to the notebook."""
		
		for node in self._traverse_tree():
			if node.is_dirty:
				self._notebook_storage.add_node(
						node_id=node.node_id,
						content_type=node.content_type,
						attributes=node.attributes,
						payloads=[]
						)
	
	def _traverse_tree(self):
		"""A generator method that yields all NotebookNodes in the notebook."""
		nodes_to_visit = [self.root]
		
		while len(nodes_to_visit) > 0:
			node = nodes_to_visit.pop()
			nodes_to_visit += node.children
			yield node
	

class NotebookNode(object):
	"""A node in a notebook. Every node has an identifier, a content type and a title.
	
	@ivar node_id: The id of the node.
	@ivar children: The node's children.
	@ivar content_type: The content type of the node.
	@ivar parent: The parent of the node.
	@ivar title: The title of the node.
	@ivar is_dirty: Indicates whether the node has changed since it was last saved.
	"""

	def __init__(self, node_id, content_type, parent, title, is_dirty=True):
		"""Constructor.
		
		@param node_id: The id of the new node.
		@param content_type: The content type of node.
		@param is_dirty: Indicates whether the node has changed since it was last saved.
		@param parent: The parent of the node or None.
		@param title: The title of the node.
		"""
		self.node_id = node_id
		self.children = []
		self.content_type = content_type
		self.is_dirty = is_dirty
		self.parent = parent
		self.title = title

	@property
	def attributes(self):
		attributes = {}
		if self.parent is not None:
			attributes[PARENT_ID_ATTRIBUTE] = self.parent.node_id
		attributes[TITLE_ATTRIBUTE] = self.title
		return attributes
	
	def new_content_child_node(self, node_id, content_type, title, main_payload, additional_payloads=None):
		"""Adds a new child node.
		
		@param node_id: The id of the new node. Must be unique within the notebook.
		@param content_type: The content type of the node.
		@param title: The title of the node.
		@param main_payload: A tuple consisting of the main paylad name and the main payload data.
		@param additional_payloads: A list containing tuples consisting of paylad names and payload data.
#		@raise NodeAlreadyExists: If a node with the same id already exists within the notebook.
		"""
		if additional_payloads is None:
			additional_payloads = []
		
		child = NotebookNode(
				node_id=node_id,
				content_type=content_type,
				new_payloads=[main_payload] + additional_payloads,
				parent=self,
				title=title)
		self.children.append(child)
		return child
	
	def __eq__(self, other):
		return \
			isinstance(other, NotebookNode) and \
			self.node_id == other.node_id and \
			self.content_type == other.content_type and \
			self.is_dirty == other.is_dirty and \
			self.parent == other.parent and \
			self.title == other.title and \
			True

	def __ne__(self, other):
		return not self.__eq__(other);

	def __repr__(self):
		return '{cls}[{node_id}, {content_type}, {dirty}, {parent}, {title}]'.format(
				cls=self.__class__.__name__,
				dirty='*' if self.is_dirty else '-',
				**self.__dict__
				)

class ContentNode(NotebookNode):
	"""A node with content in a notebook. Every content node has at least one payload and may have additional payloads.
	
	@ivar children: The node's children.
	@ivar content_type: The content type of the node.
	@ivar parent: The parent of the node.
	@ivar payload_names: The names of the payloads of the node.
	@ivar title: The title of the node.
	@ivar is_dirty: Indicates whether the node has changed since it was last saved.
	"""

	def __init__(self, node_id, content_type, parent, title, is_dirty=True, new_payloads=None, payload_names=None):
		"""Constructor.
		
		@param node_id: The id of the new node.
		@param content_type: The content type of node.
		@param is_dirty: Indicates whether the node has changed since it was last saved.
		@param new_payloads: A list containing tuples consisting of paylad names and payload data.
		@param parent: The parent of the node or None.
		@param payload_names: The names of the payloads of the node.
		@param title: The title of the node.
		"""
		self.node_id = node_id
		self.children = []
		self.content_type = content_type
		self.is_dirty = is_dirty
		self.parent = parent
		self.saved_payload_names = payload_names if payload_names is not None else []
		self.title = title
		self.unsaved_payloads = OrderedDict()
		if new_payloads is not None:
			for payload_name, payload_data in new_payloads:
				self.unsaved_payloads[payload_name] = payload_data

	def get_payload(self, payload_name):
		"""Loads a payload of the node.
		
		@param payload_name: The name of the payload.
		@return: The payload data.
#		@raise PayloadDoesNotExistError: If a payload with the same name does not exist.
#		@raise IOError: If the payload cannot be read.
		"""
		return self.unsaved_payloads[payload_name]
		
	@property
	def payload_names(self):
		return self.saved_payload_names + self.unsaved_payload_names
	
	@property
	def unsaved_payload_names(self):
		return self.unsaved_payloads.keys()

	def __eq__(self, other):
		return \
			isinstance(other, NotebookNode) and \
			self.node_id == other.node_id and \
			self.content_type == other.content_type and \
			self.is_dirty == other.is_dirty and \
			self.parent == other.parent and \
			self.saved_payload_names == other.saved_payload_names and \
			self.title == other.title and \
			self.unsaved_payloads == other.unsaved_payloads and \
			True

	def __ne__(self, other):
		return not self.__eq__(other);

	def __repr__(self):
		return '{cls}[{node_id}, {content_type}, {dirty}, {parent}, {saved_payload_names}, {title}, {unsaved_payload_names}]'.format(
				cls=self.__class__.__name__,
				dirty='*' if self.is_dirty else '-',
				**self.__dict__
				)

class InvalidStructureError(Exception):
	pass

class PayloadAlreadyExistsError(Exception):
	pass

class PayloadDoesNotExistError(Exception):
	pass

# TODO: Copyright header

import uuid

from keepnote.pref import Pref
from keepnote.notebooknew.storage import StoredNode

# Content types
CONTENT_TYPE_PAGE = u"text/html"
#CONTENT_TYPE_TRASH = u"application/x-notebook-trash"
CONTENT_TYPE_DIR = u"application/x-notebook-dir"
#CONTENT_TYPE_UNKNOWN = u"application/x-notebook-unknown"

# Attribute names
PARENT_ID_ATTRIBUTE = 'parent_id'

def _new_node_id():
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
			self._notebook_storage.add_node(node_id=node_id, content_type=CONTENT_TYPE_DIR, attributes={}, payloads=[])
			# TODO: Enable this line (a test will fail)
			#stored_nodes = self._notebook_storage.get_all_nodes()
			stored_nodes.append(StoredNode(node_id=node_id, content_type=CONTENT_TYPE_DIR, attributes={}, payload_names=[]))
		
		# Create NotebookNodes for all StoredNotes and index all StoredNotes and NotebookNodes by id.
		nodes_by_id = {}
		for stored_node in stored_nodes:
			notebook_node = NotebookNode(stored_node.node_id, stored_node.content_type, None, [])
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
		

class NotebookNode(object):
	"""A node in a notebook. Every node has an identifier, a content type, a title and may have payload.
	
	@ivar node_id: The id of the node.
	@ivar children: The node's children.
	@ivar content_type: The content type of the node.
	@ivar parent: The parent of the node.
	@ivar payload_names: The names of the payloads of the node.
	"""

	def __init__(self, node_id, content_type, parent, payload_names):
		"""Constructor.
		
		@param node_id: The id of the new node.
		@param content_type: The content type of node.
		@param parent: The parent of the node or None.
		@param payload_names: The names of the payloads of the node.
		"""
		self.node_id = node_id
		self.children = []
		self.content_type = content_type
		self.parent = parent
		self.payload_names = payload_names

	def new_child(self, node_id, content_type):
		"""Adds a new child node.
		
		@param node_id: The id of the new node. Must be unique within the notebook.
		@param content_type: The content type of the node.
#		@raise NodeAlreadyExists: If a node with the same id already exists within the notebook.
		"""
		child = NotebookNode(node_id, content_type, self, [])
		self.children.append(child)
		return child

	def __eq__(self, other):
		return \
			isinstance(other, NotebookNode) and \
			self.node_id == other.node_id and \
			self.content_type == other.content_type and \
			self.parent == other.parent and \
			self.payload_names == other.payload_names

	def __ne__(self, other):
		return not self.__eq__(other);

	def __repr__(self):
		return 'NotebookNode[{node_id}, {content_type}, {parent}, {payload_names}]'.format(
				node_id=self.node_id,
				content_type=self.content_type,
				parent=self.parent,
				payload_names=self.payload_names,
				)


class InvalidStructureError(Exception):
	pass

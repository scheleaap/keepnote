"""Memory based storage."""

import copy
import io
import logging

from keepnote.notebooknew.storage import *

__all__ = ['InMemoryStorage']

class InMemoryStorage(NotebookStorage):
	def __init__(self, *args, **kwargs):
		"""Constructor.
		"""
		self.log = logging.getLogger('{m}.{c}'.format(m=self.__class__.__module__, c=self.__class__.__name__));
		
		self.stored_notebook = StoredNotebook({})
		self.stored_nodes = {}

	def add_node(self, node_id, content_type, attributes, payloads):
		if self.has_node(node_id):
			raise NodeAlreadyExistsError()
		
		attributes = copy.deepcopy(attributes)
		stored_node = StoredNode(node_id, content_type, attributes, payload_names=[])
		stored_node.payload_files = {}
		self.stored_nodes[node_id] = stored_node
		for payload in payloads:
			self.add_node_payload(node_id, payload[0], payload[1])

	def add_node_payload(self, node_id, payload_name, payload_file):
		if not self.has_node(node_id):
			raise NodeDoesNotExistError(node_id)
		if self.has_node_payload(node_id, payload_name):
			raise PayloadAlreadyExistsError(node_id, payload_name)
		
		stored_node = self.stored_nodes[node_id]
		payload = io.BytesIO()
		payload.write(payload_file.read())
		stored_node.payload_files[payload_name] = payload
		stored_node.payload_names.append(payload_name)
	
	def get_all_nodes(self):
		for id in self.stored_nodes.keys():
			yield self.get_node(id)
	
	def get_node(self, node_id):
		if not self.has_node(node_id):
			raise NodeDoesNotExistError()
		
		return self.stored_nodes[node_id]

	def get_node_payload(self, node_id, payload_name):
		if not self.has_node(node_id):
			raise NodeDoesNotExistError(node_id)
		if not self.has_node_payload(node_id, payload_name):
			raise PayloadDoesNotExistError(node_id, payload_name)
		
		payload = self.stored_nodes[node_id].payload_files[payload_name]
		payload.seek(0)
		return payload
	
	def get_notebook(self):
		return self.stored_notebook
	
	def has_node(self, node_id):
		return node_id in self.stored_nodes
	
	def has_node_payload(self, node_id, payload_name):
		return self.has_node(node_id) and payload_name in self.stored_nodes[node_id].payload_files
		
	def remove_node(self, node_id):
		if not self.has_node(node_id):
			raise NodeDoesNotExistError()
		
		del self.stored_nodes[node_id]
		
	def remove_node_payload(self, node_id, payload_name):
		if not self.has_node(node_id):
			raise NodeDoesNotExistError(node_id)
		if not self.has_node_payload(node_id, payload_name):
			raise PayloadDoesNotExistError(node_id, payload_name)
		
		del self.stored_nodes[node_id].payload_files[payload_name]
	
	def set_node_attributes(self, node_id, attributes):
		if not self.has_node(node_id):
			raise NodeDoesNotExistError()
		
		attributes = copy.deepcopy(attributes)
		self.stored_nodes[node_id].attributes = attributes
		
	def set_notebook_attributes(self, attributes):
		attributes = copy.deepcopy(attributes)
		self.stored_notebook.attributes = attributes

	def __repr__(self):
		return '{cls}[]'.format(cls=self.__class__.__name__, **self.__dict__)

# -*- coding: utf-8 -*-
"""Base class for classes that can store notebooks."""

from __future__ import absolute_import
import hashlib

__all__ = [
		'StoredNotebook',
		'StoredNode',
		'StoredNodePayload',
		'NotebookStorage',
		'NodeAlreadyExistsError',
		'NodeDoesNotExistError',
		'ParseError',
		'PayloadAlreadyExistsError',
		'PayloadDoesNotExistError'
		]

class StoredNotebook(object):
	"""Represents a notebook stored in the NotebookStorage."""

	def __init__(self, attributes):
		"""Constructor.
		
		@param attributes: The attributes of the notebook.
		"""
		self.attributes = attributes

	def __eq__(self, other):
		return \
			isinstance(other, self.__class__) and \
			self.attributes == other.attributes

	def __ne__(self, other):
		return not self.__eq__(other);

	def __repr__(self):
		return '{cls}[{attributes}]'.format(cls=self.__class__.__name__, **self.__dict__)

class StoredNode(object):
	"""Represents a node stored in the NotebookStorage."""

	def __init__(self, node_id, content_type, attributes, payloads):
		"""Constructor.
		
		@param node_id: The id of the new node.
		@param content_type: The content type of the node.
		@param attributes: The attributes of the node.
		@param payloads: The metadata of the payloads of the node. A list of StoredNodePayload objects.
		"""
		self.node_id = node_id
		self.content_type = content_type
		self.attributes = attributes
		self.payloads = payloads
	
	def get_payload(self, payload_name):
		"""Returns a payload by name.
		
		@param payload_name: The name of the payload.
		@raise PayloadDoesNotExistError: If a payload with the name does not exist.
		"""
		filtered_payloads = [ payload for payload in self.payloads if payload.name == payload_name ]
		if filtered_payloads:
			return filtered_payloads[0]
		else:
			raise PayloadDoesNotExistError()
	
	def has_payload(self, payload_name):
		"""Returns whether a payload exists within the node.
		
		@param payload_name: The name of the payload.
		@return Whether a payload exists within the node.
		"""
		return len([ payload for payload in self.payloads if payload.name == payload_name ]) != 0

	def __eq__(self, other):
		return \
			isinstance(other, self.__class__) and \
			self.node_id == other.node_id and \
			self.content_type == other.content_type and \
			self.attributes == other.attributes and \
			self.payloads == other.payloads

	def __ne__(self, other):
		return not self.__eq__(other);

	def __repr__(self):
		return '{cls}[{node_id}, {content_type}, {attributes}, {payloads}]'.format(cls=self.__class__.__name__, **self.__dict__)

class StoredNodePayload(object):
	"""Contains payload metadata of a StoredNode."""
	
	def __init__(self, name, md5hash):
		"""Constructor.
		
		@param name: The name of the payload.
		@param md5hash: The hash of the payload.
		"""
		self.name = name
		self.md5hash = md5hash
	
	def __eq__(self, other):
		return \
			isinstance(other, self.__class__) and \
			self.name == other.name and \
			self.md5hash == other.md5hash
	
	def __ne__(self, other):
		return not self.__eq__(other);
	
	def __repr__(self):
		return '{cls}[{name}, {md5hash}]'.format(cls=self.__class__.__name__, **self.__dict__)

class NotebookStorage:
	"""Classes implementing this interface can store notebooks.
	
	All nodes within a NotebookStorage have a unique identifier.
	"""
	
	def add_node(self, node_id, content_type, attributes, payloads):
		"""Adds a new node.
		
		@param node_id: The id of the new node. Must be unique.
		@param content_type: The content type of the node.
		@param attributes: The attributes of the node.
		@param payloads: A list containing tuples consisting of paylad names and file-like objects containing payload data.
		@raise NodeAlreadyExists: If a node with the same id already exists.
		@raise IOError: If the node cannot be written.
		"""
		raise NotImplementedError(self.add_node.__name__)

	def add_node_payload(self, node_id, payload_name, payload_file):
		"""Adds a new payload to a node.
		
		@param node_id: The id of the node.
		@param payload_name: The name of the new payload. Must be unique for the node.
		@param payload_file: A file-like object with the payload data.
		@raise NodeDoesNotExistError: If a node with the id does not exist.
		@raise PayloadAlreadyExists: If a payload with the same name already exists.
		"""
		raise NotImplementedError(self.add_node_payload.__name__)

	def get_all_nodes(self):
		"""Loads the metadata of all nodes in the notebook.
		
		@return: An iterable returning StoredNode objects.
		@raise IOError: If one or nodes cannot be read.
		@raise ParseError: If the file has an invalid syntax.
		"""
		raise NotImplementedError(self.get_all_nodes.__name__)
	
	def get_node(self, node_id):
		"""Loads the metadata of a node in the notebook.
		
		@param node_id: The id of the node to be read.
		@return: A StoredNode.
		@raise NodeDoesNotExistError: If a node with the id does not exist.
		@raise IOError: If the node cannot be read.
		@raise ParseError: If the file has an invalid syntax.
		"""
		raise NotImplementedError(self.get_node.__name__)
	
	def get_node_payload(self, node_id, payload_name):
		"""Loads a payload of a node in the notebook.
		
		@param node_id: The id of the node.
		@param payload_name: The name of the payload.
		@return: A file-like object with the payload data.
		@raise NodeDoesNotExistError: If a node with the id does not exist.
		@raise PayloadDoesNotExistError: If a payload with the name does not exist.
		@raise IOError: If the payload cannot be read.
		"""
		raise NotImplementedError(self.get_node_payload.__name__)
	
	def get_notebook(self):
		"""Loads the metadata of the notebook.
		
		@return: A StoredNotebook.
		@raise IOError: If the notebook cannot be read.
		"""
		raise NotImplementedError(self.get_notebook.__name__)
		
	def has_node(self, node_id):
		"""Returns whether a node exists within the notebook.
		
		@param node_id: The id of the node.
		@return Whether a node exists within the notebook.
		"""
		raise NotImplementedError(self.has_node.__name__)
	
	def has_node_payload(self, node_id, payload_name):
		"""Returns whether a payload exists within the node.
		
		@param node_id: The id of the node.
		@param payload_name: The name of the payload.
		@return Whether a payload exists within the node.
		"""
		raise NotImplementedError(self.has_node_payload.__name__)
	
	def remove_node(self, node_id):
		"""Removes a node.
		
		@param node_id: The id of the node to remove.
		@raise NodeDoesNotExistError: If a node with the id does not exist.
		@raise IOError: If the node cannot be deleted.
		"""
		raise NotImplementedError(self.remove_node.__name__)
	
	def remove_node_payload(self, node_id, payload_name):
		"""Removes a node.
		
		@param node_id: The id of the node.
		@param payload_name: The name of the payload to remove.
		@raise NodeDoesNotExistError: If a node with the id does not exist.
		@raise PayloadDoesNotExistError: If a payload with the name does not exist.
		@raise IOError: If the payload cannot be deleted.
		"""
		raise NotImplementedError(self.remove_node_payload.__name__)
	
	def set_node_attributes(self, node_id, attributes):
		"""Sets the attributes of a node.
		
		@param node_id: The id of the node.
		@param attributes: The new attributes of the node.
		@raise NodeDoesNotExistError: If a node with the id does not exist.
		@raise IOError: If the node cannot be written.
		"""
		raise NotImplementedError(self.set_node_attributes.__name__)
	
	def set_notebook_attributes(self, attributes):
		"""Sets the attributes of the notebook.
		
		@param attributes: The new attributes of the notebook.
		@raise IOError: If the notebook cannot be written.
		"""
		raise NotImplementedError(self.set_notebook_attributes.__name__)

class NodeAlreadyExistsError(Exception):
	pass

class NodeDoesNotExistError(Exception):
	pass

class ParseError(Exception):
	pass

class PayloadAlreadyExistsError(Exception):
	pass

class PayloadDoesNotExistError(Exception):
	pass

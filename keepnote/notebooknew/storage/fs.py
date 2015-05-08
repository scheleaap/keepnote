"""File system storage."""

import io
import logging
import os
import shutil
import xml.etree.ElementTree as et

from keepnote.notebooknew.storage import *

__all__ = ['FileSystemStorage']

class FileSystemStorage(NotebookStorage):
	def __init__(self, dir):
		"""Constructor.
		
		@param dir: The path to the directory to store notes in.
		"""
		self.log = logging.getLogger('{m}.{c}'.format(m=self.__class__.__module__, c=self.__class__.__name__));
		self.dir = dir

		self.log.debug('dir={0}'.format(self.dir))
		if not os.path.exists(self.dir):
			os.makedirs(self.dir)
		
		if not os.path.exists(self._get_notebook_file_path()):
			self._write_notebook(StoredNotebook(attributes={}))

	def add_node(self, node_id, content_type, attributes, payloads):
		if self.has_node(node_id):
			raise NodeAlreadyExistsError()
		
		stored_node = StoredNode(node_id, content_type, attributes, payload_names=[])
		self._write_node(node_id, stored_node)
		for payload in payloads:
			self.add_node_payload(node_id, payload[0], payload[1])

	def add_node_payload(self, node_id, payload_name, payload_file):
		if not self.has_node(node_id):
			raise NodeDoesNotExistError(node_id)
		if self.has_node_payload(node_id, payload_name):
			raise PayloadAlreadyExistsError(node_id, payload_name)
		
		directory_path = self._get_node_payload_directory_path(node_id)
		if not os.path.exists(directory_path):
			os.makedirs(directory_path)
		
		with io.open(self._get_node_payload_file_path(node_id, payload_name), mode='wb') as f:
			f.write(payload_file.read())
		
		stored_node = self.get_node(node_id)
		stored_node.payload_names.append(payload_name)
		self._write_node(node_id, stored_node)
	
	def get_all_nodes(self):
		def handle_error(e):
			raise e
		
		for (dirpath, dirnames, filenames) in os.walk(self.dir, onerror=handle_error):
			for dirname in dirnames:
				id = dirname
				yield self.get_node(id)
	
	def get_node(self, node_id):
		if not self.has_node(node_id):
			raise NodeDoesNotExistError()
		
		return self._read_node(node_id)

	def _get_node_directory_path(self, node_id):
		return os.path.join(self.dir, node_id)
	
	def _get_node_file_path(self, node_id):
		return os.path.join(self.dir, node_id, 'node.xml')
		
	def _get_notebook_file_path(self):
		return os.path.join(self.dir, 'notebook.xml')
		
	def get_node_payload(self, node_id, payload_name):
		if not self.has_node(node_id):
			raise NodeDoesNotExistError(node_id)
		if not self.has_node_payload(node_id, payload_name):
			raise PayloadDoesNotExistError(node_id, payload_name)
		
		return io.open(self._get_node_payload_file_path(node_id, payload_name), mode='rb')
	
	def _get_node_payload_directory_path(self, node_id):
		return os.path.join(self.dir, node_id, 'payload')
		
	def _get_node_payload_file_path(self, node_id, payload_name):
		return os.path.join(self.dir, node_id, 'payload', payload_name)
	
	def get_notebook(self):
		return self._read_notebook()
	
	def has_node(self, node_id):
		return os.path.exists(self._get_node_file_path(node_id))
	
	def has_node_payload(self, node_id, payload_name):
		return os.path.exists(self._get_node_payload_file_path(node_id, payload_name))
		
	def _read_node(self, node_id):
		"""Reads a node and returns a StoredNode.
		
		@param node_id: The id of the node.
		@return: A StoredNode.
		"""
		path = self._get_node_file_path(node_id)
		
		try:
			tree = et.parse(path)
		except et.ParseError as e:
			raise ParseError(e)
		root = tree.getroot()
		node_id_el = root.find('node-id')
		if node_id_el is None:
			raise ParseError('Missing element <node-id>')
		node_id = node_id_el.text
		content_type_el = root.find('content-type')
		if content_type_el is None:
			raise ParseError('Missing element <node-id>')
		content_type = content_type_el.text
		attributes = {}
		for attribute_el in root.findall('attributes/attribute'):
			key = attribute_el.get('key')
			if key is None:
				raise ParseError('Missing attribute \'key\' in element <attribute>')
			attributes[attribute_el.get('key')] = attribute_el.text
		payload_names = []
		payload_name_els = root.findall('payload-names/payload-name')
		for payload_name_el in payload_name_els:
			payload_names.append(payload_name_el.text)
		
		return StoredNode(node_id, content_type, attributes, payload_names)
		
	def _read_notebook(self):
		"""Reads the notebook and returns a StoredNotebook.
		
		@return: A StoredNotebook.
		"""
		path = self._get_notebook_file_path()
		
		try:
			tree = et.parse(path)
		except et.ParseError as e:
			raise ParseError(e)
		root = tree.getroot()
		attributes = {}
		for attribute_el in root.findall('attributes/attribute'):
			key = attribute_el.get('key')
			if key is None:
				raise ParseError('Missing attribute \'key\' in element <attribute>')
			attributes[attribute_el.get('key')] = attribute_el.text
#		payload_names = []
#		payload_name_els = root.findall('payload-names/payload-name')
#		for payload_name_el in payload_name_els:
#			payload_names.append(payload_name_el.text)
		
		return StoredNotebook(attributes)
		
	def remove_node(self, node_id):
		if not self.has_node(node_id):
			raise NodeDoesNotExistError()
		
		shutil.rmtree(self._get_node_directory_path(node_id))
		
	def remove_node_payload(self, node_id, payload_name):
		if not self.has_node(node_id):
			raise NodeDoesNotExistError(node_id)
		if not self.has_node_payload(node_id, payload_name):
			raise PayloadDoesNotExistError(node_id, payload_name)
		
		os.remove(self._get_node_payload_file_path(node_id, payload_name))
	
	def set_node_attributes(self, node_id, attributes):
		if not self.has_node(node_id):
			raise NodeDoesNotExistError()
		
		stored_node = self._read_node(node_id)
		stored_node.attributes = attributes
		self._write_node(node_id, stored_node)
		
	def set_notebook_attributes(self, attributes):
		stored_notebook = self._read_notebook()
		stored_notebook.attributes = attributes
		self._write_notebook(stored_notebook)

	def _write_node(self, node_id, stored_node):
		"""Writes a StoredNode to a file.
		
		@param node_id: The id of the node.
		"""
		directory_path = self._get_node_directory_path(node_id)
		if not os.path.exists(directory_path):
			os.makedirs(directory_path)
		
		node_file_path = self._get_node_file_path(node_id)
		
		node_el = et.Element('node')
		et.SubElement(node_el, 'version').text = '6'
		et.SubElement(node_el, 'node-id').text = stored_node.node_id
		et.SubElement(node_el, 'content-type').text = stored_node.content_type
		
		attributes_el = et.SubElement(node_el, 'attributes')
		for (key, value) in stored_node.attributes.iteritems():
			attribute_el = et.SubElement(attributes_el, 'attribute')
			attribute_el.set('key', key)
			attribute_el.text = value
		
		payload_names_el = et.SubElement(node_el, 'payload-names')
		for payload_name in stored_node.payload_names:
			et.SubElement(payload_names_el, 'payload-name').text = payload_name

		tree = et.ElementTree(node_el)

		self.log.debug('Writing node {node_id} to {path}'.format(node_id=node_id, path=node_file_path))
		tree.write(node_file_path, encoding='utf-8', xml_declaration=True)#, pretty_print=True

	def _write_notebook(self, stored_notebook):
		"""Writes a StoredNotebook to a file.
		"""
		path = self._get_notebook_file_path()
		
		notebook_el = et.Element('notebook')
		et.SubElement(notebook_el, 'version').text = '6'
		
		attributes_el = et.SubElement(notebook_el, 'attributes')
		for (key, value) in stored_notebook.attributes.iteritems():
			attribute_el = et.SubElement(attributes_el, 'attribute')
			attribute_el.set('key', key)
			attribute_el.text = value
		
#		payload_names_el = et.SubElement(node_el, 'payload-names')
#		for payload_name in stored_node.payload_names:
#			et.SubElement(payload_names_el, 'payload-name').text = payload_name

		tree = et.ElementTree(notebook_el)

		self.log.debug('Writing notebook to {path}'.format(path=path))
		tree.write(path, encoding='utf-8', xml_declaration=True)#, pretty_print=True

	def __repr__(self):
		return '{cls}[{dir}]'.format(cls=self.__class__.__name__, **self.__dict__)

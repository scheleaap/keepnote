# -*- coding: utf-8 -*-
"""File system storage."""

from __future__ import absolute_import

import io
import hashlib
import logging
import os
import shutil
import xml.etree.ElementTree as et

from keepnote.notebooknew.storage import *
import keepnote.plist

__all__ = ['FileSystemStorage']

class FileSystemStorage(NotebookStorage):
	def __init__(self, dir):
		"""Constructor.
		
		@param dir: The path to the directory to store notes in.
		"""
		self.log = logging.getLogger('{m}.{c}'.format(m=self.__class__.__module__, c=self.__class__.__name__));
		self.dir = dir

		self.log.debug(u'dir={0}'.format(self.dir))
		if not os.path.exists(self.dir):
			os.makedirs(self.dir)
		
		if not os.path.exists(self._get_notebook_file_path()):
			self._write_notebook(StoredNotebook(attributes={}))

	def add_node(self, node_id, content_type, attributes, payloads):
		self.log.debug(u'Adding node {node_id} with content type {content_type}'.format(node_id=node_id, content_type=content_type))
		if self.has_node(node_id):
			raise NodeAlreadyExistsError()
		
		stored_node = StoredNode(node_id, content_type, attributes, payloads=[])
		self._write_node(node_id, stored_node)
		for payload in payloads:
			self.add_node_payload(node_id, payload[0], payload[1])

	def add_node_payload(self, node_id, payload_name, payload_file):
		self.log.debug(u'Adding payload "{name}" to node {node_id}'.format(node_id=node_id, name=payload_name))
		if not self.has_node(node_id):
			raise NodeDoesNotExistError(node_id)
		if self.has_node_payload(node_id, payload_name):
			raise PayloadAlreadyExistsError(node_id, payload_name)
		
		directory_path = self._get_node_payload_directory_path(node_id)
		if not os.path.exists(directory_path):
			os.makedirs(directory_path)
		
		with io.open(self._get_node_payload_file_path(node_id, payload_name), mode='wb') as f:
			data = payload_file.read()
			f.write(data)
			payload_hash = hashlib.md5(data).hexdigest()
		
		stored_node = self.get_node(node_id)
		stored_node.payloads.append(StoredNodePayload(payload_name, payload_hash))
		self._write_node(node_id, stored_node)
	
	def get_all_nodes(self):
		self.log.debug(u'Loading all nodes')
		def handle_error(e):
			raise e
		
		for (dirpath, dirnames, filenames) in os.walk(self.dir, onerror=handle_error):
			for dirname in dirnames:
				id = dirname
				self.log.debug(u'Found a node with id "{node_id}" in {path}'.format(node_id=id, path=dirpath))
				yield self.get_node(id)
			break
	
	def get_node(self, node_id):
		self.log.debug(u'Loading node {node_id}'.format(node_id=node_id))
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
		self.log.debug(u'Loading payload "{name}" of node {node_id}'.format(node_id=node_id, name=payload_name))
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
		self.log.debug(u'Loading the notebook')
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
			raise ParseError('Missing element <content-type>')
		content_type = content_type_el.text
		attributes = {}
		attributes_el = root.find('attributes')
		if attributes_el is not None:
			attributes_dict_el = None
			for child_el in attributes_el:
				attributes_dict_el = child_el
				break
			if attributes_dict_el is not None:
				attributes = self._convert_xml_subtree_to_data(attributes_dict_el)
		payloads = []
		payload_els = root.findall('payloads/payload')
		for payload_el in payload_els:
			payloads.append(StoredNodePayload(payload_el.attrib['name'], payload_el.attrib['md5hash']))
		
		return StoredNode(node_id, content_type, attributes, payloads)
		
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
#		payloads = []
#		payload_name_els = root.findall('payload-names/payload-name')
#		for payload_name_el in payload_name_els:
#			payloads.append(payload_name_el.text)
		
		return StoredNotebook(attributes)
		
	def remove_node(self, node_id):
		self.log.debug(u'Removing node {node_id}'.format(node_id=node_id))
		if not self.has_node(node_id):
			raise NodeDoesNotExistError()
		
		shutil.rmtree(self._get_node_directory_path(node_id))
		
	def remove_node_payload(self, node_id, payload_name):
		self.log.debug(u'Removing payload "{name}" from node {node_id}'.format(node_id=node_id, name=payload_name))
		if not self.has_node(node_id):
			raise NodeDoesNotExistError(node_id)
		if not self.has_node_payload(node_id, payload_name):
			raise PayloadDoesNotExistError(node_id, payload_name)
		
		os.remove(self._get_node_payload_file_path(node_id, payload_name))
		
		stored_node = self.get_node(node_id)
		stored_node.payloads[:] = [payload for payload in stored_node.payloads if payload.name != payload_name]
		self._write_node(node_id, stored_node)
	
	def set_node_attributes(self, node_id, attributes):
		self.log.debug(u'Updating attributes of node {node_id}'.format(node_id=node_id))
		if not self.has_node(node_id):
			raise NodeDoesNotExistError()
		
		stored_node = self._read_node(node_id)
		stored_node.attributes = attributes
		self._write_node(node_id, stored_node)
		
	def set_notebook_attributes(self, attributes):
		self.log.debug(u'Updating attributes of notebook')
		stored_notebook = self._read_notebook()
		stored_notebook.attributes = attributes
		self._write_notebook(stored_notebook)

	def _convert_data_to_xml_subtree(self, data):
		return keepnote.plist.dump_etree(data)
	
	def _convert_xml_subtree_to_data(self, subtree):
		return keepnote.plist.load_etree(subtree)
	
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
		attributes_el.append(self._convert_data_to_xml_subtree(stored_node.attributes))
# 		for (key, value) in stored_node.attributes.iteritems():
# 			attribute_el = et.SubElement(attributes_el, 'attribute')
# 			attribute_el.set('key', key)
# 			value_type = type(value)
# 			if value_type == str or value_type == unicode:
# 				attribute_el.set('type', 'string')
# 				attribute_el.text = value
# 			elif value_type == int:
# 				attribute_el.set('type', 'int')
# 				attribute_el.text = str(value)
# 			elif value_type == float:
# 				attribute_el.set('type', 'float')
# 				attribute_el.text = str(value)
		
		payloads_el = et.SubElement(node_el, 'payloads')
		for payload in stored_node.payloads:
			et.SubElement(payloads_el, 'payload', attrib={ 'name': payload.name, 'md5hash': payload.md5hash })

		tree = et.ElementTree(node_el)

		self.log.debug(u'Writing node {node_id} to {path}'.format(node_id=node_id, path=node_file_path))
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
		
#		payloads_el = et.SubElement(node_el, 'payload-names')
#		for payload_name in stored_node.payloads:
#			et.SubElement(payloads_el, 'payload-name').text = payload_name

		tree = et.ElementTree(notebook_el)

		self.log.debug(u'Writing notebook to {path}'.format(path=path))
		tree.write(path, encoding='utf-8', xml_declaration=True)#, pretty_print=True

	def __repr__(self):
		return '{cls}[{dir}]'.format(cls=self.__class__.__name__, **self.__dict__)

# -*- coding: utf-8 -*-

from collections import namedtuple
from datetime import datetime
from functools import partial
import hashlib
import io
from pytz import utc
import sys

from keepnote.notebooknew import ContentNode, FolderNode, TrashNode, CONTENT_TYPE_FOLDER, CONTENT_TYPE_TRASH,\
	NotebookNodePayload
from keepnote.notebooknew.storage import StoredNode, StoredNodePayload

__all__ = [
		'Dao',
		'NotebookNodeDao',
		'ContentNodeDao',
		'FolderNodeDao',
		'StoredNodePayloadWithData',
		'ReadFromStorageWriteToMemoryPayload',
		'TrashNodeDao',
		'InvalidStructureError',
		]

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
		value = attributes[attribute_definition.key]
		if attribute_definition.type == 'string':
			return value
		elif attribute_definition.type == 'int':
			return int(value)
		elif attribute_definition.type == 'timestamp':
			dt = datetime.fromtimestamp(int(value), tz=utc)
			return dt
		else:
			return value
	else:
		return attribute_definition.default


class StoredNodePayloadWithData(StoredNodePayload):
	"""Contains payload metadata and optionally the payload data of a StoredNode."""
	
	def __init__(self, name, md5hash, data_reader):
		"""Constructor.
		
		@param name: The name of the payload.
		@param md5hash: The MD5 hash of the payload data.
		@param data_reader: A function that returns the a file-like object containing the payload data.
		"""
		super(StoredNodePayloadWithData, self).__init__(name, md5hash)
		self.get_data = data_reader
	
	def has_data(self):
		return self.get_data is not None
	
	def __eq__(self, other):
		return \
			isinstance(other, StoredNodePayloadWithData) and \
			self.name == other.name and \
			self.md5hash == other.md5hash and \
			self.get_data == other.get_data
	
	def __ne__(self, other):
		return not self.__eq__(other);
	
	def __repr__(self):
		return 'StoredNodePayloadWithData[{name}, {md5hash}, has_data={has_data}]'.format(has_data=self.has_data(), **self.__dict__)


class Dao(object):
	"""TODO"""
	
	def __init__(self, notebook, notebook_storage, node_daos):
		"""TODO"""
		self._notebook = notebook
		self._notebook_storage = notebook_storage
		self._node_daos = node_daos
		
		self._last_remote_node_versions = []
		self._last_local_node_versions = []
	
	def sync(self):
		now = datetime.now(tz=utc)
		
		# Load all remote StoredNodes.
		remote_sns_by_id = { sn.node_id: sn for sn in self._notebook_storage.get_all_nodes() }
		remote_ids = set(remote_sns_by_id.iterkeys())
		
		# Load all local NotebookNode and convert them to StoredNodes.
		local_sns_by_id = { nn.node_id: self._convert_nn_to_sn(nn) for nn in self._notebook._traverse_tree() if not nn.is_deleted }
		local_ids = set(local_sns_by_id.iterkeys())
		
		deleted_in_local = set([ node_id for node_id in remote_ids if node_id not in local_sns_by_id and node_id in self._last_local_node_versions])
		new_in_remote = set([ node_id for node_id in remote_ids if node_id not in local_sns_by_id and node_id not in self._last_local_node_versions])
		new_in_local = set([ node_id for node_id in local_ids if node_id not in remote_sns_by_id])
		others = local_ids - deleted_in_local - new_in_remote - new_in_local
		
		self._add_new_in_remote_to_local(remote_sns_by_id, new_in_remote)
		self._add_new_in_local_to_remote(local_sns_by_id, new_in_local)
		self._remove_deleted_in_local_from_remote(deleted_in_local)
		for node_id in others:
			remote_sn = remote_sns_by_id[node_id]
			local_sn = local_sns_by_id[node_id]
			if remote_sn != local_sn:
				# We're assuming only local changes can happen.
				
				self._notebook_storage.set_node_attributes(node_id, local_sn.attributes)
				for local_payload in local_sn.payloads:
					if remote_sn.has_payload(local_payload.name) and remote_sn.get_payload(local_payload.name).md5hash != local_payload.md5hash:
						# TODO: Replace with set_payload() or update_node()
						self._notebook_storage.remove_node_payload(node_id, local_payload.name)
						with local_payload.get_data() as f:
							self._notebook_storage.add_node_payload(node_id, local_payload.name, f)
		
		self._last_local_node_versions = local_sns_by_id.keys()
		
	
	def _add_new_in_local_to_remote(self, sns_by_id, node_ids):
		for node_id in node_ids:
			sn = sns_by_id[node_id]
			payloads = [ (payload.name, payload.get_data()) for payload in sn.payloads]
			try:
				self._notebook_storage.add_node(
						node_id=sn.node_id,
						content_type=sn.content_type,
						attributes=sn.attributes,
						payloads=payloads,
						)
			finally:
				for payload in payloads:
					payload[1].close()
	
	def _add_new_in_remote_to_local(self, sns_by_id, node_ids):
		# Create NotebookNodes for all StoredNotes and index all StoredNotes and NotebookNodes by id.
		nns_by_id = {}
		for node_id in node_ids:
			sn = sns_by_id[node_id]
			nn = self._convert_sn_to_nn(sn)
			nns_by_id[sn.node_id] = (sn, nn)
		
		# Create the NotebookNode tree structure.
		for stored_node, notebook_node in nns_by_id.values():
			parent_id = get_attribute_value(PARENT_ID_ATTRIBUTE, stored_node.attributes)
			if parent_id is not None:
				if parent_id not in nns_by_id:
					raise InvalidStructureError('Node {child_id} has no parent {parent_id}'.format(
							child_id=stored_node.node_id, parent_id=parent_id))
				elif parent_id == stored_node.node_id:
					raise InvalidStructureError('Node {node_id} references itself as parent'.format(
							node_id=stored_node.node_id))
				else:
					# Check for cycles.
					temp_parent_notebook_node = nns_by_id[parent_id][1]
					while temp_parent_notebook_node.parent is not None:
						temp_parent_notebook_node = temp_parent_notebook_node.parent
						
						if temp_parent_notebook_node.node_id == stored_node.node_id:
							raise InvalidStructureError('Node {node_id} indirectly references itself as parent'.format(
									node_id=stored_node.node_id))
					
				parent_notebook_node = nns_by_id[parent_id][1]
				notebook_node.parent = parent_notebook_node
				parent_notebook_node._add_child_node(notebook_node)
			else:
				if self._notebook.root is not None:
					raise InvalidStructureError('Multiple root nodes found')
				self._notebook.root = notebook_node
			if notebook_node.content_type == CONTENT_TYPE_TRASH:
				self._notebook.trash = notebook_node
# 		
# 		# If no root node exists, create it.
# 		if self._notebook.root is None:
# 			notebook_node = FolderNode(
# 					notebook_storage=self._notebook_storage,
# 					notebook=self,
# 					parent=None,
# 					title=TITLE_ATTRIBUTE.default,
# 					loaded_from_storage=False
# 					)
# 			self._notebook.root = notebook_node
#
# 		# If no trash node exists, create it.
# 		if self._notebook.trash is None:
# 			notebook_node = TrashNode(
# 					notebook_storage=self._notebook_storage,
# 					notebook=self,
# 					parent=self._notebook.root,
# 					title=TITLE_ATTRIBUTE.default,
# 					loaded_from_storage=False
# 					)
# 			self._notebook.root._add_child_node(notebook_node)
# 			self._notebook.trash = notebook_node
# 		
# 		if self._notebook.trash.parent is not self._notebook.root:
# 			raise InvalidStructureError('The trash node is not a direct child of the root node')
		
		# Sort children by their id.
		for stored_node, notebook_node in nns_by_id.values():
			notebook_node._children.sort(key=lambda child_notebook_node: child_notebook_node.node_id)
	
	def _convert_nn_to_sn(self, nn):
		for node_dao in self._node_daos:
			if node_dao.accepts(nn.content_type):
				sn = node_dao.nn_to_sn(nn)
				return sn
		raise StoredNodeConversionError('There is no node DAO that accepts the content type {content_type}'.format(
				content_type=sn.content_type))
		
	def _convert_sn_to_nn(self, sn):
		for node_dao in self._node_daos:
			if node_dao.accepts(sn.content_type):
				nn = node_dao.sn_to_nn(sn, self._notebook_storage, self._notebook)
				return nn
		raise StoredNodeConversionError('There is no node DAO that accepts the content type {content_type}'.format(
				content_type=sn.content_type))
	
	def _remove_deleted_in_local_from_remote(self, node_ids):
		for node_id in node_ids:
			self._notebook_storage.remove_node(node_id)


class NotebookNodeDao(object):
	"""TODO"""
	
	def accepts(self, content_type):
		"""Returns whether this class can convert nodes of the given content type.
		
		@param content_type: The content type which needs to be converted.
		@return: A boolean.
		"""
		raise NotImplementedError('TODO')
	
	def sn_to_nn(self, sn, notebook_storage, notebook):
		"""TODO"""
		raise NotImplementedError('TODO')


class ContentNodeDao(NotebookNodeDao):
	"""TODO"""
	
	def accepts(self, content_type):
		return True
	
	def nn_to_sn(self, nn):
		attributes = {
				MAIN_PAYLOAD_NAME_ATTRIBUTE.key: nn.main_payload_name,
				TITLE_ATTRIBUTE.key: nn.title,
				CLIENT_PREFERENCES_ATTRIBUTE.key: nn.client_preferences._data,
				}
		if nn.parent is not None:
			attributes[PARENT_ID_ATTRIBUTE.key] = nn.parent.node_id
		if nn.icon_normal is not None:
			attributes[ICON_NORMAL_ATTRIBUTE.key] = nn.icon_normal
		if nn.icon_open is not None:
			attributes[ICON_OPEN_ATTRIBUTE.key] = nn.icon_open
		if nn.title_color_foreground is not None:
			attributes[TITLE_COLOR_FOREGROUND_ATTRIBUTE.key] = nn.title_color_foreground
		if nn.title_color_background is not None:
			attributes[TITLE_COLOR_BACKGROUND_ATTRIBUTE.key] = nn.title_color_background
		if nn.created_time is not None:
			attributes[CREATED_TIME_ATTRIBUTE.key] = datetime_to_timestamp(nn.created_time)
		if nn.modified_time is not None:
			attributes[MODIFIED_TIME_ATTRIBUTE.key] = datetime_to_timestamp(nn.modified_time)
		
		payloads = []
		for payload in nn.payloads.itervalues():
			payloads.append(StoredNodePayloadWithData(
					name=payload.name,
					md5hash=payload.get_md5hash(),
					data_reader=partial(payload.open, mode='r'),
					))
		
		return StoredNode(nn.node_id, nn.content_type, attributes, payloads=payloads)
	
	def sn_to_nn(self, sn, notebook_storage, notebook):
		title = get_attribute_value(TITLE_ATTRIBUTE, sn.attributes)
		created_time = get_attribute_value(CREATED_TIME_ATTRIBUTE, sn.attributes)
		modified_time = get_attribute_value(MODIFIED_TIME_ATTRIBUTE, sn.attributes)
# 		order = get_attribute_value(ORDER_ATTRIBUTE, sn.attributes)
		icon_normal = get_attribute_value(ICON_NORMAL_ATTRIBUTE, sn.attributes)
		icon_open = get_attribute_value(ICON_OPEN_ATTRIBUTE, sn.attributes)
		title_color_foreground = get_attribute_value(TITLE_COLOR_FOREGROUND_ATTRIBUTE, sn.attributes)
		title_color_background = get_attribute_value(TITLE_COLOR_BACKGROUND_ATTRIBUTE, sn.attributes)
		client_preferences = get_attribute_value(CLIENT_PREFERENCES_ATTRIBUTE, sn.attributes)
		
		if not sn.payloads:
			raise InvalidStructureError('Content node {node_id} has no payload'.format(
					node_id=sn.node_id))
			
		main_payload_name = get_attribute_value(MAIN_PAYLOAD_NAME_ATTRIBUTE, sn.attributes)
		
		if main_payload_name is None:
			raise InvalidStructureError('Missing attribute \'{attribute}\' in content node {node_id}'.format(
					node_id=sn.node_id,
					attribute=MAIN_PAYLOAD_NAME_ATTRIBUTE.key))
		elif main_payload_name not in [ payload.name for payload in sn.payloads ]:
			raise InvalidStructureError(
					'The main payload with name \'{main_payload_name}\' is missing in content node {node_id}'.format(
							node_id=sn.node_id,
							main_payload_name=main_payload_name))
		
		main_payload = ReadFromStorageWriteToMemoryPayload(
				name=main_payload_name,
				original_reader=lambda: notebook_storage.get_node_payload(sn.node_id, main_payload_name),
				original_md5hash='whazzup',
				)
		additional_payloads = [
				ReadFromStorageWriteToMemoryPayload(
						name=additional_payload_name,
						original_reader=lambda: notebook_storage.get_node_payload('whatev', 'dog'),#(sn.node_id, additional_payload_name),
						original_md5hash='whazzup',
						)
				for additional_payload_name in sn.payloads if additional_payload_name != main_payload_name
				]
		nn = ContentNode(
				notebook_storage=notebook_storage,
				notebook=notebook,
				content_type=sn.content_type,
				parent=None,
				loaded_from_storage=True,
				title=title,
# 				order=order,
				icon_normal=icon_normal,
				icon_open=icon_open,
				title_color_foreground=title_color_foreground,
				title_color_background=title_color_background,
				client_preferences=client_preferences,
				main_payload=main_payload,
				additional_payloads=additional_payloads,
				node_id=sn.node_id,
				created_time=created_time,
				modified_time=modified_time,
				)
		
		return nn


class FolderNodeDao(NotebookNodeDao):
	"""TODO"""
	
	def accepts(self, content_type):
		return content_type == CONTENT_TYPE_FOLDER
	
	def sn_to_nn(self, sn, notebook_storage, notebook):
		title = get_attribute_value(TITLE_ATTRIBUTE, sn.attributes)
		created_time = get_attribute_value(CREATED_TIME_ATTRIBUTE, sn.attributes)
		modified_time = get_attribute_value(MODIFIED_TIME_ATTRIBUTE, sn.attributes)
		order = get_attribute_value(ORDER_ATTRIBUTE, sn.attributes)
		icon_normal = get_attribute_value(ICON_NORMAL_ATTRIBUTE, sn.attributes)
		icon_open = get_attribute_value(ICON_OPEN_ATTRIBUTE, sn.attributes)
		title_color_foreground = get_attribute_value(TITLE_COLOR_FOREGROUND_ATTRIBUTE, sn.attributes)
		title_color_background = get_attribute_value(TITLE_COLOR_BACKGROUND_ATTRIBUTE, sn.attributes)
		
		nn = FolderNode(
				notebook_storage=notebook_storage,
				notebook=notebook,
				parent=None,
				loaded_from_storage=True,
				title=title,
				order=order,
				icon_normal=icon_normal,
				icon_open=icon_open,
				title_color_foreground=title_color_foreground,
				title_color_background=title_color_background,
				node_id=sn.node_id,
				created_time=created_time,
				modified_time=modified_time,
				)
		
		return nn


class ReadFromStorageWriteToMemoryPayload(NotebookNodePayload):
	"""A NotebookNodePayload that returns the original payload data or the changed data if the payload has been written.

	open(mode='r') will return the result of original_reader() als long as open(mode='w') has not been called or if
	reset() has been called afterwards. Otherwise, it will return the last data that was written using open(mode='w').
	
	The changed payload data is kept in memory.
	
	@ivar name: The name of the payload.
	@ivar md5hash: The name of the payload.
	"""
	
	class CapturingBytesIO(io.BytesIO):
		def __init__(self, on_close_handler, *args, **kwargs):
			super(ReadFromStorageWriteToMemoryPayload.CapturingBytesIO, self).__init__(*args, **kwargs)
			self.on_close_handler = on_close_handler
		
		def close(self, *args, **kwargs):
			self.on_close_handler(self.getvalue())
			return io.BytesIO.close(self, *args, **kwargs)
	
	def __init__(self, name, original_reader, original_md5hash):
		"""Constructor.
		
		@param name: The name of the payload.
		@param original_reader: A function that returns a file-like object containing the original payload data.
		@param original_md5hash: The hash of the original payload data.
		""" 
		super(ReadFromStorageWriteToMemoryPayload, self).__init__(
				name=name,
				)
		self.original_reader = original_reader
		self.original_md5hash = original_md5hash
		self.new_data = None
		self.md5hash = self.original_md5hash
	
	def open(self, mode='r'):
		if mode == 'w':
			def on_close(new_data):
				self.new_data = new_data
				self.md5hash = hashlib.md5(self.new_data).hexdigest()
			return ReadFromStorageWriteToMemoryPayload.CapturingBytesIO(on_close)
		else:
			if self.new_data is not None:
				return io.BytesIO(self.new_data)
			else:
				return self.original_reader()
	
	def reset(self):
		"""Removes the new data."""
		self.new_data = None
		self.md5hash = self.original_md5hash


class TrashNodeDao(NotebookNodeDao):
	"""TODO"""
	
	def accepts(self, content_type):
		return content_type == CONTENT_TYPE_TRASH
	
	def sn_to_nn(self, sn, notebook_storage, notebook):
		title = get_attribute_value(TITLE_ATTRIBUTE, sn.attributes)
		created_time = get_attribute_value(CREATED_TIME_ATTRIBUTE, sn.attributes)
		modified_time = get_attribute_value(MODIFIED_TIME_ATTRIBUTE, sn.attributes)
		order = get_attribute_value(ORDER_ATTRIBUTE, sn.attributes)
		icon_normal = get_attribute_value(ICON_NORMAL_ATTRIBUTE, sn.attributes)
		icon_open = get_attribute_value(ICON_OPEN_ATTRIBUTE, sn.attributes)
		title_color_foreground = get_attribute_value(TITLE_COLOR_FOREGROUND_ATTRIBUTE, sn.attributes)
		title_color_background = get_attribute_value(TITLE_COLOR_BACKGROUND_ATTRIBUTE, sn.attributes)
		
		nn = TrashNode(
				notebook_storage=notebook_storage,
				notebook=notebook,
				parent=None,
				loaded_from_storage=True,
				title=title,
				order=order,
				icon_normal=icon_normal,
				icon_open=icon_open,
				title_color_foreground=title_color_foreground,
				title_color_background=title_color_background,
				node_id=sn.node_id,
				created_time=created_time,
				modified_time=modified_time,
				)
		
		return nn
		

class DaoError(Exception):
	pass


class InvalidStructureError(DaoError):
	pass


class StoredNodeConversionError(DaoError):
	pass

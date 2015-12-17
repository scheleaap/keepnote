# -*- coding: utf-8 -*-

from collections import namedtuple
from datetime import datetime
from pytz import utc
import sys

from keepnote.notebooknew import NotebookNode, ContentNode, FolderNode, TrashNode, CONTENT_TYPE_FOLDER, CONTENT_TYPE_TRASH

__all__ = [
		'Dao',
		'StorageNode',
		'StorageNodePayload',
		'NotebookNodeDao',
		'ContentNodeDao',
		'FolderNodeDao',
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


class StorageNode(object):
	"""Represents a node that is or can be stored in a NotebookStorage."""

	def __init__(self, node_id, content_type, attributes, payloads):
		"""Constructor.
		
		@param node_id: The id of the new node.
		@param content_type: The content type of the node.
		@param attributes: The attributes of the node.
		@param payloads: The payloads of the node.
		"""
		self.node_id = node_id
		self.content_type = content_type
		self.attributes = attributes
		self.payloads = payloads
	
	def __eq__(self, other):
		return \
			isinstance(other, StorageNode) and \
			self.node_id == other.node_id and \
			self.content_type == other.content_type and \
			self.attributes == other.attributes and \
			self.payloads == other.payloads
	
	def __ne__(self, other):
		return not self.__eq__(other);
	
	def __repr__(self):
		return 'StorageNode[{node_id}, {content_type}, {attributes}, {payloads}]'.format(**self.__dict__)


class StorageNodePayload(object):
	"""Contains payload metadata and optionally the payload itself of a StorageNode."""
	
	def __init__(self, name, data):
		self.name = name
		self.data = data
	
	def has_data(self):
		return self.data is not None
	
	def __eq__(self, other):
		return \
			isinstance(other, StorageNodePayload) and \
			self.name == other.name and \
			self.data == other.data
	
	def __ne__(self, other):
		return not self.__eq__(other);
	
	def __repr__(self):
		return 'StorageNodePayload[{name}]'.format(**self.__dict__)


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
		
		# Load all remote StorageNodes.
		remote_sns_by_id = { sn.node_id: sn for sn in self._notebook_storage.get_all_nodes() }
		remote_ids = set(remote_sns_by_id.iterkeys())
		
		# Load all local NotebookNode and convert them to StorageNodes.
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
		
		self._last_local_node_versions = local_sns_by_id.keys()
		
	
	def _add_new_in_local_to_remote(self, sns_by_id, node_ids):
		for node_id in node_ids:
			sn = sns_by_id[node_id]
			self._notebook_storage.add_node(
					node_id=sn.node_id,
					content_type=sn.content_type,
					attributes=sn.attributes,
# 					payloads=sn.payloads)
					payloads=[])
	
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
		raise StorageNodeConversionError('There is no node DAO that accepts the content type {content_type}'.format(
				content_type=sn.content_type))
		
	def _convert_sn_to_nn(self, sn):
		for node_dao in self._node_daos:
			if node_dao.accepts(sn.content_type):
				nn = node_dao.sn_to_nn(sn, self._notebook_storage, self._notebook)
				return nn
		raise StorageNodeConversionError('There is no node DAO that accepts the content type {content_type}'.format(
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
# 				MAIN_PAYLOAD_NAME_ATTRIBUTE.key: nn.main_payload_name,
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
		
		return StorageNode(nn.node_id, nn.content_type, attributes, [])
	
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
		
		if not sn.payload_names:
			raise InvalidStructureError('Content node {node_id} has no payload'.format(
					node_id=sn.node_id))
			
		main_payload_name = get_attribute_value(MAIN_PAYLOAD_NAME_ATTRIBUTE, sn.attributes)
		
		if main_payload_name is None:
			raise InvalidStructureError('Missing attribute \'{attribute}\' in content node {node_id}'.format(
					node_id=sn.node_id,
					attribute=MAIN_PAYLOAD_NAME_ATTRIBUTE.key))
		elif main_payload_name not in sn.payload_names:
			raise InvalidStructureError(
					'The main payload with name \'{main_payload_name}\' is missing in content node {node_id}'.format(
							node_id=sn.node_id,
							main_payload_name=main_payload_name))
		
		additional_payload_names = [payload_name for payload_name in sn.payload_names if payload_name != main_payload_name]
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
				node_id=sn.node_id,
				created_time=created_time,
				modified_time=modified_time,
				main_payload_name=main_payload_name,
				additional_payload_names=additional_payload_names,
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


class StorageNodeConversionError(DaoError):
	pass

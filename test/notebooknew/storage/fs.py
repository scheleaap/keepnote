# -*- coding: utf-8 -*-

from __future__ import absolute_import
import io
import os

from keepnote.notebooknew.storage import StoredNodePayload, ParseError
from keepnote.notebooknew.storage.fs import FileSystemStorage
from ...base import TestBase
from . import DEFAULT_ID, DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA, DEFAULT_HTML_PAYLOAD_HASH, NotebookStorageTestBase, add_node, create_stored_node

class FileSystemStorageTest(TestBase, NotebookStorageTestBase):
    def create_notebook_storage(self):
        return FileSystemStorage(dir=self.notebookdir)

    def test_fs_repr(self):
        s = FileSystemStorage(dir=self.notebookdir)
        repr(s)

    def test_fs_notebook_dirs_created(self):
        notebookdir = os.path.join(self.notebookdir, 'subdir1', 'subdir2')
        FileSystemStorage(dir=notebookdir)

        self.assertTrue(os.path.exists(notebookdir), 'Notebook directory does not exist')

    def test_fs_notebook_dirs_existing(self):
        assert not os.path.exists(self.notebookdir)
        os.makedirs(self.notebookdir)
        assert os.path.exists(self.notebookdir)

        FileSystemStorage(dir=self.notebookdir)
        # No exception expected here.

    def test_fs_notebook_xml_created(self):
        FileSystemStorage(dir=self.notebookdir)

        self.assertTrue(os.path.exists(os.path.join(self.notebookdir, 'notebook.xml')), 'Notebook XML does not exist')

    def test_fs_get_node_invalid_xml(self):
        s = FileSystemStorage(dir=self.notebookdir)

        # Add the node manually first.
        path = s._get_node_file_path(DEFAULT_ID)
        os.makedirs(os.path.dirname(path))
        with open(path, 'w+') as f:
            f.write(
"""<?xml version='1.0' encoding='utf-8'?>
<node>
    <version>6</version>
    <node-id>my_id_1</node-id>
    <content-type>text/html</content-type>
    <a
</node>
""")

        # Then read it.
        with self.assertRaises(ParseError):
            s.get_node(DEFAULT_ID)

    def test_fs_get_node_missing_node_id(self):
        s = FileSystemStorage(dir=self.notebookdir)

        # Add the node manually first.
        path = s._get_node_file_path(DEFAULT_ID)
        os.makedirs(os.path.dirname(path))
        with open(path, 'w+') as f:
            f.write(
"""<?xml version='1.0' encoding='utf-8'?>
<node>
    <version>6</version>
    <!--<node-id>my_id_1</node-id>-->
    <content-type>text/html</content-type>
</node>
""")

        # Then read it.
        with self.assertRaises(ParseError):
            s.get_node(DEFAULT_ID)

    def test_fs_get_node_missing_content_type(self):
        s = FileSystemStorage(dir=self.notebookdir)

        # Add the node manually first.
        path = s._get_node_file_path(DEFAULT_ID)
        os.makedirs(os.path.dirname(path))
        with open(path, 'w+') as f:
            f.write(
"""<?xml version='1.0' encoding='utf-8'?>
<node>
    <version>6</version>
    <node-id>my_id_1</node-id>
    <!--<content-type>text/html</content-type>-->
</node>
""")

        # Then read it.
        with self.assertRaises(ParseError):
            s.get_node(DEFAULT_ID)

    def test_fs_get_node_missing_attributes(self):
        s = FileSystemStorage(dir=self.notebookdir)

        # Add the node manually first.
        path = s._get_node_file_path(DEFAULT_ID)
        os.makedirs(os.path.dirname(path))
        with open(path, 'w+') as f:
            f.write(
"""<?xml version='1.0' encoding='utf-8'?>
<node>
    <version>6</version>
    <node-id>my_id_1</node-id>
    <content-type>text/html</content-type>
</node>
""")

        # Then read it.
        s.get_node(DEFAULT_ID)

    def test_fs_get_node_missing_attribute_contents(self):
        s = FileSystemStorage(dir=self.notebookdir)

        # Add the node manually first.
        path = s._get_node_file_path(DEFAULT_ID)
        os.makedirs(os.path.dirname(path))
        with open(path, 'w+') as f:
            f.write(
"""<?xml version='1.0' encoding='utf-8'?>
<node>
    <version>6</version>
    <node-id>my_id_1</node-id>
    <content-type>text/html</content-type>
    <attributes>
    </attributes>
</node>
""")

        # Then read it.
        s.get_node(DEFAULT_ID)

    def test_fs_node_structure(self):
        # self.keep_tmpdir=True

        # Create a node with payload.
        s = FileSystemStorage(dir=self.notebookdir)
        id_ = add_node(s, payloads=[(DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA))], payload_paths=[])

        node_directory = os.path.join(self.notebookdir, id_)
        node_file = os.path.join(node_directory, 'node.xml')
        payload_directory = os.path.join(node_directory, 'payload')
        payload_file = os.path.join(payload_directory, DEFAULT_HTML_PAYLOAD_NAME)

        # Verify that the expected directory and files exist.
        self.assertTrue(os.path.exists(node_directory), 'Node directory does not exist')
        self.assertTrue(os.path.exists(node_file), 'Node file does not exist')
        self.assertTrue(os.path.exists(payload_directory), 'Payload directory does not exist')
        self.assertTrue(os.path.exists(payload_file), 'Payload file does not exist')

    def test_fs_remove_node_directory_removed(self):
        # Create a node with payload.
        s = FileSystemStorage(dir=self.notebookdir)
        id_ = add_node(s, payloads=[(DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA))], payload_paths=[])

        # Remove the node.
        s.remove_node(id_)

        # Verify that the node directory does not exist.
        node_directory = os.path.join(self.notebookdir, id_)
        self.assertFalse(os.path.exists(node_directory), 'Node directory still exists')

    def test_fs_add_node_payload_node_xml(self):
        # Create a node with a payload called 'node.xml'.
        s = FileSystemStorage(dir=self.notebookdir)
        id_ = add_node(s, payloads=[('node.xml', io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA))], payload_paths=[])

        # Then read them.
        s = FileSystemStorage(dir=self.notebookdir)
        self.assertEqual(create_stored_node(payloads=[StoredNodePayload('node.xml', DEFAULT_HTML_PAYLOAD_HASH)]), s.get_node(id_))
        self.assertEqual(s.get_node_payload(id_, 'node.xml').read(), DEFAULT_HTML_PAYLOAD_DATA)

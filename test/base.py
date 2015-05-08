import logging
import os
import shutil
import tempfile
import unittest

"""
TODO:
If RANDOM_TEMP_DIRS is False, keep but empty the directories
"""

class TestBase(unittest.TestCase):
	RANDOM_TEMP_DIRS = False

	def __init__(self, *args, **kwargs):
		super(TestBase, self).__init__(*args, **kwargs)
		self.tmpdir = None

	@classmethod
	def setUpClass(cls):
		parentdir = os.path.dirname(os.path.dirname(__file__))

		# Clean up old testing directories.
		for d in os.listdir(parentdir):
			if os.path.isdir(d) and d.startswith('test_'):
				shutil.rmtree(d)

	def setUp(self, *args, **kwargs):
		super(TestBase, self).setUp(*args, **kwargs)

		logging.basicConfig(
			level=logging.DEBUG,
			format='%(levelname)s %(name)s.%(funcName)s() %(message)s',
			)
		logging.getLogger('keepnote.notebook.storage.FileSystemStorage').setLevel(logging.INFO)

		parentdir = os.path.dirname(os.path.dirname(__file__))
		parentdir = unicode(parentdir) # This causes all paths derived from parentdir to be unicode strings as well.

		if TestBase.RANDOM_TEMP_DIRS:
			self.tmpdir = tempfile.mkdtemp(dir=parentdir, prefix='test_')
		else:
			self.tmpdir = os.path.join(parentdir, self._testMethodName)
			if self._testMethodName == 'test':
				self.tmpdir += '_test'
			if os.path.exists(self.tmpdir):
				shutil.rmtree(self.tmpdir)
			os.makedirs(self.tmpdir)
		self.assertTrue(os.path.exists(self.tmpdir))
		self.notebookdir = os.path.join(self.tmpdir, 'book')
		self.assertTrue(not os.path.exists(self.notebookdir))
		self.keep_tmpdir = False

	def tearDown(self, *args, **kwargs):
		super(TestBase, self).tearDown(*args, **kwargs)

		if self.keep_tmpdir is False:
			if self.tmpdir is not None:
				shutil.rmtree(self.tmpdir)
			self.assertTrue(not os.path.exists(self.tmpdir))

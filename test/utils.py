"""Utility functions for unit tests."""

def assertFileObjectEquals(self, first, second):
	"""Fails if the two file-like objects' contents are not equal."""
	
	data_first = first.read()
	data_second = second.read() 
	self.assertEquals(data_first, data_second)

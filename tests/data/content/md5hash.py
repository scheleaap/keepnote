#!/usr/bin/env python

import argparse
import hashlib
import io
import logging

if __name__ == '__main__':
    # Parse command-line options.
    args = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter
            )
    args.add_argument('file', help='The file to process.')
    args = args.parse_args()
    
    # Initialize logging.
    logging.basicConfig(
            level=logging.WARN,
            format='%(levelname)s %(message)s',
            )
    
    with io.open(args.file, 'rb') as f:
        data = f.read()
    
    hash = hashlib.md5(data).hexdigest()
    
    print('{file}: {hash}'.format(file=args.file, hash=hash))

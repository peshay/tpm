#!/usr/bin/env python
"""Setup to install TeamPasswordManager API Python Module."""
from distutils.core import setup
setup(name='tpm',
      version='1.0',
      py_modules=['tpm'],
      install_requires=['requests'],
      description='Provides functions to work with TeamPasswordManager API.',
      url='https://github.com/peshay/tpm',
      author='Andreas Hubert, censhare AG',
      author_email='andreas.hubert@censhare.com',
      license='MIT',
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'Topic :: Software Development :: API Tools',
                   'License :: OSI Approved :: MIT License',
                   'Programming Language :: Python :: 2.7', ],
      keywords='TeamPasswordManager json api',

      )

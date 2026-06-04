#!/usr/bin/env python
"""Setup to install TeamPasswordManager API Python Module."""
from distutils.core import setup
setup(name='tpm',
      version='4.2',
      py_modules=['tpm'],
      install_requires=['requests>=2.33.0', 'future', 'urllib3'],
      description='Provides functions to work with TeamPasswordManager API.',
      url='https://github.com/peshay/tpm',
      author='Andreas Hubert',
      author_email='anhubert@gmail.com',
      license='MIT',
      python_requires='>=3.8',
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'Topic :: Software Development :: Libraries :: Application '
                   'Frameworks',
                   'License :: OSI Approved :: MIT License',
                   'Programming Language :: Python :: 3.8',
                   'Programming Language :: Python :: 3.9',
                   'Programming Language :: Python :: 3.10',
                   'Programming Language :: Python :: 3.11',
                   'Programming Language :: Python :: 3.12'],
      keywords='TeamPasswordManager json api',
      )

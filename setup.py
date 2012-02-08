# -*- encoding: utf8 -*-
from setuptools import setup, find_packages

import os

setup(
    name = "django-prefetch",
    version = "0.1.1",
    url = 'https://github.com/ionelmc/django-prefetch',
    download_url = '',
    license = 'BSD',
    description = "Generic model related data prefetch framework for Django",
    long_description = file(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    author = 'Ionel Cristian Mărieș',
    author_email = 'contact@ionelmc.ro',
    packages = find_packages('src'),
    package_dir = {'':'src'},
    py_modules = ['prefetch'],
    include_package_data = True,
    zip_safe = False,
    classifiers = [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)

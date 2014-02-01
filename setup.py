# -*- encoding: utf8 -*-
import os

from setuptools import find_packages, setup

setup(
    name="django-prefetch",
    version="0.2",
    url='https://github.com/ionelmc/django-prefetch',
    download_url='',
    license='BSD',
    description="Generic model related data prefetch framework for Django",
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    author='Ionel Cristian Mărieș',
    author_email='contact@ionelmc.ro',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=['prefetch'],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    install_requires=['Django>=1.1']
)

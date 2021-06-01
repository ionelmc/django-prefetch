========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |requires|
        | |coveralls| |codecov|
        | |scrutinizer| |codacy| |codeclimate|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/django-prefetch/badge/?style=flat
    :target: https://django-prefetch.readthedocs.io/
    :alt: Documentation Status

.. |travis| image:: https://api.travis-ci.com/ionelmc/django-prefetch.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.com/github/ionelmc/django-prefetch

.. |requires| image:: https://requires.io/github/ionelmc/django-prefetch/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/ionelmc/django-prefetch/requirements/?branch=master

.. |coveralls| image:: https://coveralls.io/repos/ionelmc/django-prefetch/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/r/ionelmc/django-prefetch

.. |codecov| image:: https://codecov.io/gh/ionelmc/django-prefetch/branch/master/graphs/badge.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/ionelmc/django-prefetch

.. |codacy| image:: https://img.shields.io/codacy/grade/11d1f80103ca434db15e2804b61c522f.svg
    :target: https://www.codacy.com/app/ionelmc/django-prefetch
    :alt: Codacy Code Quality Status

.. |codeclimate| image:: https://codeclimate.com/github/ionelmc/django-prefetch/badges/gpa.svg
   :target: https://codeclimate.com/github/ionelmc/django-prefetch
   :alt: CodeClimate Quality Status

.. |version| image:: https://img.shields.io/pypi/v/django-prefetch.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/django-prefetch

.. |wheel| image:: https://img.shields.io/pypi/wheel/django-prefetch.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/django-prefetch

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/django-prefetch.svg
    :alt: Supported versions
    :target: https://pypi.org/project/django-prefetch

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/django-prefetch.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/django-prefetch

.. |commits-since| image:: https://img.shields.io/github/commits-since/ionelmc/django-prefetch/v1.2.3.svg
    :alt: Commits since latest release
    :target: https://github.com/ionelmc/django-prefetch/compare/v1.2.3...master


.. |scrutinizer| image:: https://img.shields.io/scrutinizer/quality/g/ionelmc/django-prefetch/master.svg
    :alt: Scrutinizer Status
    :target: https://scrutinizer-ci.com/g/ionelmc/django-prefetch/


.. end-badges

Simple and generic model related data prefetch framework for Django solving the "1+N queries" problem that happens when
you need related data for your objects.

In most of the cases you'll have forward relations (foreign keys to something)
and can use select_related to fetch that data on the same query. However, in
some cases you cannot design your models that way and need data from reverse
relations (models that have foreign keys to your objects).

Django has prefetch_related_ for this, however, this framework provides greater
flexibility than Django's prefetch_related_ queryset method at the cost
of writting the mapping and query functions for the data. This has the advantage
that you can do things prefetch_related_ cannot (see the latest_book example_
below).

* Free software: BSD license

.. _prefetch_related: https://docs.djangoproject.com/en/dev/ref/models/querysets/#prefetch-related

Installation guide
==================

Install it::

    pip install django-prefetch

Use it as your model's default manager (or as a base class if you have custom
manager).

Requirements
============

:OS: Any
:Runtime: Python 2.7, 3.3+ or PyPy
:Packages: Django>=1.9

Example
=======

Here's a simple example of models and prefetch setup::

    from django.db import models
    from prefetch import PrefetchManager, Prefetcher

    class Author(models.Model):
        name = models.CharField(max_length=100)

        objects = PrefetchManager(
            books = Prefetcher(
                filter = lambda ids: Book.objects.filter(author__in=ids),
                reverse_mapper = lambda book: [book.author_id],
                decorator = lambda author, books=(): setattr(author, 'books', books)
            ),
            latest_book = Prefetcher(
                filter = lambda ids: Book.objects.filter(author__in=ids),
                reverse_mapper = lambda book: [book.author_id],
                decorator = lambda author, books=(): setattr(
                    author,
                    'latest_book',
                    max(books, key=lambda book: book.created) if books else None
                )
            )
        )

    class Book(models.Model):
        class Meta:
            get_latest_by = 'created'

        name = models.CharField(max_length=100)
        created = models.DateTimeField(auto_now_add=True)
        author = models.ForeignKey(Author)

Use it like this::

    for a in Author.objects.prefetch('books', 'latest_book'):
        print a.books
        print a.latest_book

Prefetcher arguments
--------------------

Example models::

    class LatestNBooks(Prefetcher):
        def __init__(self, count=2):
            self.count = count

        def filter(self, ids):
            return Book.objects.filter(author__in=ids)

        def reverse_mapper(self, book):
            return [book.author_id]

        def decorator(self, author, books=()):
            books = sorted(books, key=lambda book: book.created, reverse=True)
            setattr(author,
                    'latest_%s_books' % self.count,
                    books[:self.count])

    class Author(models.Model):
        name = models.CharField(max_length=100)

        objects = PrefetchManager(
            latest_n_books = LatestNBooks
        )


Use it like this::

    from prefetch import P

    for a in Author.objects.prefetch(P('latest_n_books', count=5)):
        print a.latest_5_book

.. note::

    ``P`` is optional and you can only use for prefetch definitions that are Prefetcher subclasses. You can't use it with prefetcher-instance style
    definitions like in the first example. Don't worry, if you do, you will get an exception explaining what's wrong.


Other examples
--------------

Check out the tests for more examples.

TODO
====

* Document ``collect`` option of ``Prefetcher``
* Create tests covering custom ``collect`` and ``mapper``

Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox

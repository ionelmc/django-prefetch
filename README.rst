===========================
      django-prefetch
===========================

.. image:: http://img.shields.io/travis/ionelmc/django-prefetch/master.png
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/ionelmc/django-prefetch

.. image:: https://ci.appveyor.com/api/projects/status/qg7n1s6urm9q11i3/branch/master
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/ionelmc/django-prefetch

.. image:: http://img.shields.io/coveralls/ionelmc/django-prefetch/master.png
    :alt: Coverage Status
    :target: https://coveralls.io/r/ionelmc/django-prefetch

.. image:: http://img.shields.io/pypi/v/django-prefetch.png
    :alt: PYPI Package
    :target: https://pypi.python.org/pypi/django-prefetch

.. image:: http://img.shields.io/pypi/dm/django-prefetch.png
    :alt: PYPI Package
    :target: https://pypi.python.org/pypi/django-prefetch

Simple and generic model related data prefetch framework for Django solving the
"1+N queries" problem that happens when you need related data for your objects.

In most of the cases you'll have forward relations (foreign keys to something)
and can use select_related to fetch that data on the same query. However, in
some cases you cannot design your models that way and need data from reverse
relations (models that have foreign keys to your objects).

Django 1.4 has prefetch_related_ for this, however, this framework provides greater
flexibility than Django 1.4's prefetch_related_ queryset method at the cost
of writting the mapping and query functions for the data. This has the advantage
that you can do things prefetch_related_ cannot (see the latest_book example_
bellow).

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
:Runtime: Python 2.6, 2.7, 3.2, 3.3 or PyPy
:Packages: Django>=1.1 (including 1.7)

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
                    max(books, key=lambda book: book.created)
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

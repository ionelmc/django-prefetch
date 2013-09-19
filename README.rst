===========================
    django-prefetch
===========================

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

The project has been tested on Django 1.1, 1.2, 1.3, 1.4 and trunk with Python
2.6 and 2.7.

.. image:: https://secure.travis-ci.org/ionelmc/django-prefetch.png
    :alt: Build Status
    :target: http://travis-ci.org/ionelmc/django-prefetch

.. image:: https://coveralls.io/repos/ionelmc/django-prefetch/badge.png?branch=master
    :alt: Coverage Status
    :target: https://coveralls.io/r/ionelmc/django-prefetch

Example
=======

Here's a simple example of models and prefetch setup:

.. code-block:: python

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

Use it like this:

.. code-block:: python

    for a in Author.objects.prefetch('books', 'latest_book'):
        print a.books
        print a.latest_book

Prefetcher arguments
--------------------

Example models:

.. code-block:: python

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


Use it like this:

.. code-block:: python

    from prefetch import P

    for a in Author.objects.prefetch(P('latest_n_books', count=5)):
        print a.latest_5_book

.. note::

    ``P`` is optional and you can only use for prefetch definitions that are Prefetcher subclasses. You can't use it with prefetcher-instance style
    definitions like in the first example. Don't worry, if you do, you will get an exception explaining what's wrong.


Other examples
--------------

Check out the tests for more examples.


.. image:: https://d2weczhvl823v0.cloudfront.net/ionelmc/django-prefetch/trend.png
   :alt: Bitdeli badge
   :target: https://bitdeli.com/free


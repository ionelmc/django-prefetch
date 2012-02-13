===========================
    django-prefetch
===========================


Generic model related data prefetch framework for Django. Provides greater
flexibility than Django 1.4's `prefetch_related`__ queryset method at the cost
of writting the mapping fuctions for the data.

__ https://docs.djangoproject.com/en/dev/ref/models/querysets/#prefetch-related

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
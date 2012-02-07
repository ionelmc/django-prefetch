===========================
    django-prefetch
===========================


Generic model related data prefetch framework for Django. Provides greater
flexibility than Django 1.4's prefetch_related queryset method at the cost
writting the mapping fuctions for the data.

Installation guide
==================

Install it::

    pip install django-prefetch

Use it as your model's default manager (or as a base class if you have custom
manager).

Example
=======

Here's a rather elaborate example with a fallback on regular 1+n queries (if you
don't call ``prefetch`` on the queryset)::

    from django.db import models
    from prefetch import PrefetchManager, Prefetcher
    
    class Author(models.Model):
        name = models.CharField(max_length=100)
    
        objects = PrefetchManager(
            books = Prefetcher(
                filter = lambda ids: Book.objects.filter(author__in=ids),
                reverse_mapper = lambda book: [book.author_id],
                decorator = lambda author, books=(): setattr(author, 'prefetched_books', books)
            ),
            latest_book = Prefetcher(
                filter = lambda ids: Book.objects.filter(author__in=ids),
                reverse_mapper = lambda book: [book.author_id],
                decorator = lambda author, books=(): setattr(
                    author,
                    'prefetched_latest_book',
                    max(books, lambda book: book.created)
                )
            )
        )
        
        @property
        def books(self):
            if hasattr(self, 'prefetched_books'):
                return self.prefetched_books
            else:
                return self.book_set.all()
        
        @property
        def latest_book(self):
            if hasattr(self, 'prefetched_latest_book'):
                return self.prefetched_latest_book
            else:
                return self.book_set.latest()
    
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

Requirements
============

The project has been tested on Django 1.1, 1.2, 1.3, 1.4 and trunk with Python
2.6 and 2.7.

TODO
====

 * document ``collect`` option of ``Prefetcher``
 * create tests covering custom ``collect`` and ``mapper``
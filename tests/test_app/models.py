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

class Tag(models.Model):
    name = models.CharField(max_length=100)

class Book(models.Model):
    class Meta:
        get_latest_by = 'created'

    name = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Author)
    tags = models.ManyToManyField(Tag)
    

from django import VERSION
from django.db import models
from prefetch import PrefetchManager, Prefetcher

class SillyException(Exception):
    pass

class SillyPrefetcher(Prefetcher):
    def filter(ids): 
        raise SillyException()
    def reverse_mapper(book):
        raise SillyException()
    def decorator(author, books=()): 
        raise SillyException()
    
    

class Author(models.Model):
    name = models.CharField(max_length=100)

    objects = PrefetchManager(
        books = Prefetcher(
            filter = lambda ids: Book.objects.filter(author__in=ids),
            mapper = lambda author: author.id,
            reverse_mapper = lambda book: [book.author_id],
            decorator = lambda author, books=(): setattr(author, 'prefetched_books', books)
        ),
        latest_book = Prefetcher(
            filter = lambda ids: Book.objects.filter(author__in=ids),
            reverse_mapper = lambda book: [book.author_id],
            decorator = lambda author, books=(): setattr(
                author,
                'prefetched_latest_book',
                max(books, key=lambda book: book.created) if books else None
            )
        ),
        silly = SillyPrefetcher()
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
            try:
                return self.book_set.latest()
            except Book.DoesNotExist:
                return

class Tag(models.Model):
    name = models.CharField(max_length=100)

if VERSION < (1, 2):
    class Book_Tag(models.Model):
        book = models.ForeignKey("Book")
        tag = models.ForeignKey("Tag")

class Publisher(models.Model):
    name = models.CharField(max_length=100)

class Book(models.Model):
    class Meta:
        get_latest_by = 'created'

    name = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Author)
    publisher = models.ForeignKey(Publisher, null=True)
    
    if VERSION < (1, 2):
        tags = models.ManyToManyField(Tag, through="Book_Tag")
    else:
        tags = models.ManyToManyField(Tag)
    
    objects = PrefetchManager(
        tags = Prefetcher(
            filter = lambda ids: (Book_Tag if VERSION < (1, 2) else Book.tags.through).objects.filter(book__in=ids),
            reverse_mapper = lambda book_tag: [book_tag.book_id],
            decorator = lambda user, book_tags=():
                setattr(user, 'prefetched_tags', [i.tag for i in book_tags])
        )
    )
    
    @property
    def selected_tags(self):
        if hasattr(self, 'prefetched_tags'):
            return self.prefetched_tags
        else:
            return self.tags.all()

class BookNote(models.Model):
    book = models.ForeignKey("Book")
    notes = models.TextField()

    objects = PrefetchManager()
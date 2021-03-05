from django.db import models

from prefetch import Prefetcher
from prefetch import PrefetchManager


class SillyException(Exception):
    pass


class SillyPrefetcher(Prefetcher):
    def filter(ids):
        raise SillyException()

    def reverse_mapper(book):
        raise SillyException()

    def decorator(author, books=()):
        raise SillyException()


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
                'prefetched_latest_%s_books' % self.count,
                books[:self.count])


class LatestBook(Prefetcher):
    def filter(self, ids):
        return Book.objects.filter(author__in=ids)

    def reverse_mapper(self, book):
        return [book.author_id]

    def decorator(self, author, books=()):
        setattr(
            author,
            'prefetched_latest_book',
            max(books, key=lambda book: book.created) if books else None
        )


class Author(models.Model):
    name = models.CharField(max_length=100)

    objects = PrefetchManager(
        books=Prefetcher(
            filter=lambda ids: Book.objects.filter(author__in=ids),
            mapper=lambda author: author.id,
            reverse_mapper=lambda book: [book.author_id],
            decorator=lambda author, books=():
            setattr(author, 'prefetched_books', books)
        ),
        latest_n_books=LatestNBooks,
        latest_book_as_class=LatestBook,
        latest_book=Prefetcher(
            filter=lambda ids: Book.objects.filter(author__in=ids),
            reverse_mapper=lambda book: [book.author_id],
            decorator=lambda author, books=(): setattr(
                author,
                'prefetched_latest_book',
                max(books, key=lambda book: book.created) if books else None
            )
        ),
        silly=SillyPrefetcher,
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


class Publisher(models.Model):
    name = models.CharField(max_length=100)


class Book(models.Model):
    class Meta:
        get_latest_by = 'created'

    name = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Author, models.CASCADE)
    publisher = models.ForeignKey(Publisher, models.CASCADE, null=True)

    tags = models.ManyToManyField(Tag)

    objects = PrefetchManager(
        tags=Prefetcher(
            filter=lambda ids: Book.tags.through.objects.select_related('tag').filter(book__in=ids),
            reverse_mapper=lambda book_tag: [book_tag.book_id],
            decorator=lambda user, book_tags=():
            setattr(user, 'prefetched_tags', [i.tag for i in book_tags])
        ),
        similar_books=Prefetcher(
            filter=lambda ids: Book.objects.filter(author__in=ids),
            mapper=lambda book: book.author_id,
            reverse_mapper=lambda book: [book.author_id],
            decorator=lambda book, books=():
            setattr(book.author, 'prefetched_books', books),
            collect=True,
        ),
        similar_books_missing_collect=Prefetcher(
            filter=lambda ids: Book.objects.filter(author__in=ids),
            mapper=lambda book: book.author_id,
            reverse_mapper=lambda book: [book.author_id],
            decorator=lambda book, books=():
            setattr(book.author, 'prefetched_books', books),
        ),
    )

    @property
    def similar_books(self):
        if hasattr(self.author, 'prefetched_books'):
            return [i for i in self.author.prefetched_books if i != self]
        else:
            return Book.objects.filter(
                author=self.author_id
            ).exclude(
                id=self.id
            )

    @property
    def selected_tags(self):
        if hasattr(self, 'prefetched_tags'):
            return self.prefetched_tags
        else:
            return self.tags.all()


class BookNote(models.Model):
    book = models.ForeignKey("Book", models.CASCADE, null=True)
    bogus = models.ForeignKey("Book", models.CASCADE, null=True, related_name="+")
    notes = models.TextField()

    objects = PrefetchManager()

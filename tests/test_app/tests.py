from django import VERSION
from django.test import TestCase

from .models import Book, Author, Tag, BookNote
from prefetch import InvalidPrefetch, Prefetcher

class PrefetchTests(TestCase):
    def test_books(self):
        author = Author.objects.create(name="John Doe")
        for i in range(3):
            Book.objects.create(name="Book %s"%i, author=author)

        for i in Author.objects.prefetch('books').filter(pk=author.pk):
            self.assertTrue(hasattr(i, 'prefetched_books'))
            self.assertEquals(len(i.books), 3, i.books) 

        for i in Author.objects.filter(pk=author.pk):
            self.assertFalse(hasattr(i, 'prefetched_books'))
            self.assertEquals(len(i.books), 3, i.books) 

    def test_latest_book(self):
        author1 = Author.objects.create(name="Johnny")
        author2 = Author.objects.create(name="Johnny")
        for i in range(3, 6):
            Book.objects.create(name="Book %s"%i, author=author1)

        for i in Author.objects.prefetch('latest_book').filter(pk=author1.pk):
            self.assertTrue(hasattr(i, 'prefetched_latest_book'))
            self.assertEquals(i.latest_book.name, "Book 5", i) 

        for i in Author.objects.prefetch('latest_book').filter(pk=author2.pk):
            self.assertTrue(hasattr(i, 'prefetched_latest_book'))
            self.assertEquals(i.latest_book, None, i) 

        for i in Author.objects.filter(pk=author1.pk):
            self.assertFalse(hasattr(i, 'prefetched_latest_book'))
            self.assertEquals(i.latest_book.name, "Book 5", i) 
    
        for i in Author.objects.filter(pk=author2.pk):
            self.assertFalse(hasattr(i, 'prefetched_latest_book'))
            self.assertEquals(i.latest_book, None, i) 

    def test_forwarders(self):
        author = Author.objects.create(name="Johnny")
        tags = []
        for i in range(100):
            tags.append(Tag.objects.create(name="Tag %s" % i))

        for i in range(10, 20):
            book = Book.objects.create(name="Book %s"%i, author=author)
            if VERSION < (1, 2):
                from .models import Book_Tag
                for tag in tags[::7]:
                    Book_Tag.objects.create(tag=tag, book=book)
            else:
                book.tags.add(*tags[::7])
            
            for j in range(3):
                BookNote.objects.create(notes="Note %s/%s" % (i, j), book=book)
        
        for note in BookNote.objects.select_related("book").prefetch("book__tags"):
            self.assertTrue(hasattr(note.book, 'prefetched_tags'))
            self.assertEquals(len(note.book.selected_tags), 15, i)
            self.assertEquals(set(note.book.selected_tags), set(tags[::7]), i)

        for note in BookNote.objects.select_related("book"):
            self.assertFalse(hasattr(note.book, 'prefetched_tags'))
            self.assertEquals(len(note.book.selected_tags), 15, i)
            self.assertEquals(set(note.book.selected_tags), set(tags[::7]), i)

    def test_tags(self):
        tags = []
        for i in range(100):
            tags.append(Tag.objects.create(name="Tag %s" % i))
        author = Author.objects.create(name="Johnny")
        book = Book.objects.create(name="TaggedBook", author=author)
        if VERSION < (1, 2):
            from .models import Book_Tag
            for tag in tags[::7]:
                Book_Tag.objects.create(tag=tag, book=book)
        else:
            book.tags.add(*tags[::7])
        
        for i in Book.objects.prefetch('tags').filter(pk=book.pk):
            self.assertTrue(hasattr(i, 'prefetched_tags'))
            self.assertEquals(len(i.selected_tags), 15, i)
            self.assertEquals(set(i.selected_tags), set(tags[::7]), i)

        for i in Book.objects.filter(pk=book.pk):
            self.assertFalse(hasattr(i, 'prefetched_tags'))
            self.assertEquals(len(i.selected_tags), 15, i)
            self.assertEquals(set(i.selected_tags), set(tags[::7]), i)
    
    def test_books_queryset_get(self):
        author = Author.objects.create(name="John Doe")
        for i in range(3):
            Book.objects.create(name="Book %s"%i, author=author)

        i = Author.objects.prefetch('books').get(pk=author.pk)
        self.assertTrue(hasattr(i, 'prefetched_books'))
        self.assertEquals(len(i.books), 3, i.books) 
    
        i = Author.objects.get(name="John Doe")
        self.assertFalse(hasattr(i, 'prefetched_books'))
        self.assertEquals(len(i.books), 3, i.books) 
    
    if VERSION >= (1, 2):
        def test_using_db(self):
            author = Author.objects.using('secondary').create(name="John Doe")
            for i in range(3):
                Book.objects.using('secondary').create(name="Book %s"%i, author=author)

            for i in Author.objects.prefetch('books').filter(pk=author.pk).using('secondary'):
                self.assertTrue(hasattr(i, 'prefetched_books'))
                self.assertEquals(len(i.books), 3, i.books) 

            for i in Author.objects.using('secondary').prefetch('books').filter(pk=author.pk):
                self.assertTrue(hasattr(i, 'prefetched_books'))
                self.assertEquals(len(i.books), 3, i.books) 

            for i in Author.objects.filter(pk=author.pk).using('secondary'):
                self.assertFalse(hasattr(i, 'prefetched_books'))
                self.assertEquals(len(i.books), 3, i.books) 

    def test_wrong_prefetch_fwd(self):
        self.assertRaises(InvalidPrefetch, lambda: Book.objects.prefetch('author__asdf'))

    def test_wrong_prefetch(self):
        self.assertRaises(InvalidPrefetch, lambda: Author.objects.prefetch('asdf'))

    def test_wrong_definitions(self):
        class Bad1(Prefetcher):
            pass
        class Bad2(Bad1):
            def filter(self, ids):
                pass
        class Bad3(Bad2):
            def reverse_mapper(self, obj):
                pass
            
        self.assertRaises(RuntimeError, Bad1)
        self.assertRaises(RuntimeError, Bad2)
        self.assertRaises(RuntimeError, Bad3)
        
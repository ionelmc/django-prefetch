import logging
import logging.handlers

from django import VERSION
from django.test import TestCase

from .models import Book, Author, Tag, BookNote, SillyException
from prefetch import InvalidPrefetch, Prefetcher

class AssertingHandler(logging.handlers.BufferingHandler):

    def __init__(self,capacity):
        logging.handlers.BufferingHandler.__init__(self,capacity)

    def assertLogged(self, test_case, msg):
        for record in self.buffer:
            s = self.format(record)
            if s.startswith(msg):
                return
        test_case.assertTrue(False, "Failed to find log message: " + msg)

class _AssertRaisesContext(object):
    """A context manager used to implement TestCase.assertRaises* methods."""

    def __init__(self, expected, test_case, expected_regexp=None):
        self.expected = expected
        self.failureException = test_case.failureException
        self.expected_regexp = expected_regexp

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is None:
            try:
                exc_name = self.expected.__name__
            except AttributeError:
                exc_name = str(self.expected)
            raise self.failureException(
                "{0} not raised".format(exc_name))
        if not issubclass(exc_type, self.expected):
            # let unexpected exceptions pass through
            return False
        self.exception = exc_value # store for later retrieval
        if self.expected_regexp is None:
            return True

        expected_regexp = self.expected_regexp
        if isinstance(expected_regexp, basestring):
            expected_regexp = re.compile(expected_regexp)
        if not expected_regexp.search(str(exc_value)):
            raise self.failureException('"%s" does not match "%s"' %
                     (expected_regexp.pattern, str(exc_value)))
        return True

class PrefetchTests(TestCase):
    def assertRaises(self, excClass, callableObj=None, *args, **kwargs):
        """Fail unless an exception of class excClass is thrown
           by callableObj when invoked with arguments args and keyword
           arguments kwargs. If a different type of exception is
           thrown, it will not be caught, and the test case will be
           deemed to have suffered an error, exactly as for an
           unexpected exception.

           If called with callableObj omitted or None, will return a
           context object used like this::

                with self.assertRaises(SomeException):
                    do_something()

           The context manager keeps a reference to the exception as
           the 'exception' attribute. This allows you to inspect the
           exception after the assertion::

               with self.assertRaises(SomeException) as cm:
                   do_something()
               the_exception = cm.exception
               self.assertEqual(the_exception.error_code, 3)
        """
        context = _AssertRaisesContext(excClass, self)
        if callableObj is None:
            return context
        with context:
            callableObj(*args, **kwargs)
    
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

    def test_forwarders_with_null(self):
        author = Author.objects.create(name="Johnny")
        book = Book.objects.create(name="Book", author=author)
        BookNote.objects.create(notes="Note 1", book=book)
        BookNote.objects.create(notes="Note 2")
        
        note1, note2 = BookNote.objects.select_related("book").prefetch("book__tags").order_by('notes')
        self.assertTrue(hasattr(note1.book, 'prefetched_tags'))
        self.assertEquals(len(note1.book.selected_tags), 0)
        self.assertEquals(note2.book, None)

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

            for i in Author.objects.db_manager('secondary').prefetch('books').filter(pk=author.pk):
                self.assertTrue(hasattr(i, 'prefetched_books'))
                self.assertEquals(len(i.books), 3, i.books) 

            for i in Author.objects.filter(pk=author.pk).using('secondary'):
                self.assertFalse(hasattr(i, 'prefetched_books'))
                self.assertEquals(len(i.books), 3, i.books) 

    def test_wrong_prefetch_fwd(self):
        with self.assertRaises(InvalidPrefetch) as cm:
            Book.objects.prefetch('author__asdf')
            
        self.assertEquals(cm.exception.args, ("Invalid part asdf in prefetch call for author__asdf on model <class 'test_app.models.Book'>. The name is not a prefetcher nor a forward relation (fk).",))

    def test_wrong_prefetch_after_miss(self):
        with self.assertRaises(InvalidPrefetch) as cm:
            Book.objects.prefetch('author')
        
        self.assertEquals(cm.exception.args, ("Invalid prefetch call with author for on model <class 'test_app.models.Book'>. The last part isn't a prefetch definition.",))

    def test_wrong_prefetch_after_wrong(self):
        with self.assertRaises(InvalidPrefetch) as cm:
            Author.objects.prefetch('books__asdf')
        
        self.assertEquals(cm.exception.args, ("Invalid part asdf in prefetch call for books__asdf on model <class 'test_app.models.Author'>. You cannot have any more relations after the prefetcher.",))

    def test_wrong_prefetch_fwd_no_manager(self):
        with self.assertRaises(InvalidPrefetch) as cm:
            Book.objects.prefetch('publisher__whatev')
            
        self.assertEquals(cm.exception.args, ("Manager for <class 'test_app.models.Publisher'> is not a PrefetchManager instance.",))

    def test_wrong_prefetch(self):
        with self.assertRaises(InvalidPrefetch) as cm:
            Author.objects.prefetch('asdf')
            
        self.assertEquals(cm.exception.args, ("Invalid part asdf in prefetch call for asdf on model <class 'test_app.models.Author'>. The name is not a prefetcher nor a forward relation (fk).",))

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
    
    def test_exception_raising_definitions(self):
        author = Author.objects.create(name="John Doe")
        
        asserting_handler = AssertingHandler(10)
        logging.getLogger().addHandler(asserting_handler)

        self.assertRaises(SillyException, lambda: list(Author.objects.prefetch('silly')))

        asserting_handler.assertLogged(self, "Prefetch failed for silly prefetch on the Author model:\nTraceback (most recent call last):")
        logging.getLogger().removeHandler(asserting_handler)

        

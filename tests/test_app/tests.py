import logging
import logging.handlers
import re
import time
import warnings

from django.test import TestCase

from prefetch import InvalidPrefetch
from prefetch import P
from prefetch import Prefetcher
from prefetch import PrefetchManager

from .models import Author
from .models import Book
from .models import BookNote
from .models import LatestBook
from .models import SillyException
from .models import Tag


class AssertingHandler(logging.handlers.BufferingHandler):

    def __init__(self, capacity):
        logging.handlers.BufferingHandler.__init__(self, capacity)

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
        self.exception = exc_value  # store for later retrieval
        if self.expected_regexp is None:
            return True

        expected_regexp = self.expected_regexp
        if isinstance(expected_regexp, basestring):  # noqa
            expected_regexp = re.compile(expected_regexp)
        if not expected_regexp.search(str(exc_value)):
            raise self.failureException('"%s" does not match "%s"' %
                                        (expected_regexp.pattern, str(exc_value)))
        return True


class PrefetchTests(TestCase):
    databases = ['default', 'secondary']

    def setUp(self):
        super(PrefetchTests, self).setUp()
        warnings.simplefilter('error')

    def tearDown(self):
        super(PrefetchTests, self).tearDown()
        warnings.resetwarnings()

    def assertRegexpMatches(self, text, expected_regexp, msg=None):
        """Fail the test unless the text matches the regular expression."""
        if isinstance(expected_regexp, str):
            expected_regexp = re.compile(expected_regexp)
        if not expected_regexp.search(text):
            msg = msg or "Regexp didn't match"
            msg = '%s: %r not found in %r' % (msg, expected_regexp.pattern, text)
            raise self.failureException(msg)

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
            Book.objects.create(name="Book %s" % i, author=author)

        for i in Author.objects.prefetch('books').filter(pk=author.pk):
            self.assertTrue(hasattr(i, 'prefetched_books'))
            self.assertEqual(len(i.books), 3, i.books)

        for i in Author.objects.filter(pk=author.pk):
            self.assertFalse(hasattr(i, 'prefetched_books'))
            self.assertEqual(len(i.books), 3, i.books)

    def test_latest_n_books(self):
        author1 = Author.objects.create(name="Johnny")
        for i in range(20, 30):
            Book.objects.create(name="Book %s" % i, author=author1)
            time.sleep(0.05)

        for i in Author.objects.prefetch('latest_n_books').filter(pk=author1.pk):
            self.assertTrue(hasattr(i, 'prefetched_latest_2_books'))
            self.assertEqual(
                [j.name for j in i.prefetched_latest_2_books],
                ["Book 29", "Book 28"]
            )

        for i in Author.objects.prefetch(P('latest_n_books')).filter(pk=author1.pk):
            self.assertTrue(hasattr(i, 'prefetched_latest_2_books'))
            self.assertEqual(
                [j.name for j in i.prefetched_latest_2_books],
                ["Book 29", "Book 28"]
            )

        for i in Author.objects.prefetch(P('latest_n_books', 5)).filter(pk=author1.pk):
            self.assertTrue(hasattr(i, 'prefetched_latest_5_books'))
            self.assertEqual(
                [j.name for j in i.prefetched_latest_5_books],
                ["Book 29", "Book 28", "Book 27", "Book 26", "Book 25"]
            )

        for i in Author.objects.prefetch(P('latest_n_books', count=5)).filter(pk=author1.pk):
            self.assertTrue(hasattr(i, 'prefetched_latest_5_books'))
            self.assertEqual(
                [j.name for j in i.prefetched_latest_5_books],
                ["Book 29", "Book 28", "Book 27", "Book 26", "Book 25"]
            )

    def test_clone(self):
        Author.objects.all()._clone()

    def test_latest_book(self):
        author1 = Author.objects.create(name="Johnny")
        author2 = Author.objects.create(name="Johnny")
        for i in range(3, 6):
            Book.objects.create(name="Book %s" % i, author=author1)
            time.sleep(0.1)

        for i in Author.objects.prefetch('latest_book').filter(pk=author1.pk):
            self.assertTrue(hasattr(i, 'prefetched_latest_book'))
            self.assertEqual(i.latest_book.name, "Book 5", i.latest_book.name)

        for i in Author.objects.prefetch('latest_book_as_class').filter(pk=author1.pk):
            self.assertTrue(hasattr(i, 'prefetched_latest_book'))
            self.assertEqual(i.latest_book.name, "Book 5", i)

        for i in Author.objects.prefetch('latest_book_as_class').filter(pk=author2.pk):
            self.assertTrue(hasattr(i, 'prefetched_latest_book'))
            self.assertEqual(i.latest_book, None, i)

        for i in Author.objects.filter(pk=author1.pk):
            self.assertFalse(hasattr(i, 'prefetched_latest_book'))
            self.assertEqual(i.latest_book.name, "Book 5", i)

        for i in Author.objects.filter(pk=author2.pk):
            self.assertFalse(hasattr(i, 'prefetched_latest_book'))
            self.assertEqual(i.latest_book, None, i)

    def test_forwarders(self):
        author = Author.objects.create(name="Johnny")
        tags = []
        for i in range(100):
            tags.append(Tag.objects.create(name="Tag %s" % i))

        for i in range(10, 20):
            book = Book.objects.create(name="Book %s" % i, author=author)
            book.tags.add(*tags[::7])

            for j in range(3):
                BookNote.objects.create(notes="Note %s/%s" % (i, j), book=book, bogus=book)

        with self.assertNumQueries(2):
            for note in BookNote.objects.select_related("book", "bogus").prefetch("book__tags"):
                self.assertTrue(hasattr(note.book, 'prefetched_tags'))
                self.assertEqual(len(note.book.selected_tags), 15, i)
                self.assertEqual(set(note.book.selected_tags), set(tags[::7]), i)
                self.assertTrue(isinstance(note.bogus, Book))

        for note in BookNote.objects.select_related("book"):
            self.assertFalse(hasattr(note.book, 'prefetched_tags'))
            self.assertEqual(len(note.book.selected_tags), 15, i)
            self.assertEqual(set(note.book.selected_tags), set(tags[::7]), i)

    def test_manual_forwarders_aka_collect(self):
        authors = [
            Author.objects.create(name="Johnny-%s" % i) for i in range(20)
        ]

        for author in authors:
            for i in range(20, 25):
                book = Book.objects.create(name="Book %s" % i, author=author)

        for book in Book.objects.select_related('author').prefetch('similar_books'):
            self.assertTrue(hasattr(book.author, 'prefetched_books'))
            self.assertEqual(len(book.similar_books), 4, book.similar_books)
            self.assertEqual(
                set(book.similar_books),
                set(Book.objects.filter(
                    author=book.author_id
                ).exclude(
                    id=book.id
                ))
            )

        failed = 0
        for book in Book.objects.select_related('author').prefetch('similar_books_missing_collect'):
            self.assertTrue(hasattr(book.author, 'prefetched_books'))
            if len(book.similar_books) != 4:
                failed += 1
        self.assertTrue(failed > 0,
                        "There's should be at least 1 failure for similar_books_missing_collect prefetcher.")

        for book in Book.objects.select_related('author'):
            self.assertFalse(hasattr(book.author, 'prefetched_books'))
            self.assertEqual(len(book.similar_books), 4, book.similar_books)
            self.assertEqual(
                set(book.similar_books),
                set(Book.objects.filter(
                    author=book.author_id
                ).exclude(
                    id=book.id
                ))
            )

    def test_forwarders_with_null(self):
        author = Author.objects.create(name="Johnny")
        book = Book.objects.create(name="Book", author=author)
        BookNote.objects.create(notes="Note 1", book=book)
        BookNote.objects.create(notes="Note 2")

        note1, note2 = BookNote.objects.select_related("book").prefetch("book__tags").order_by('notes')
        self.assertTrue(hasattr(note1.book, 'prefetched_tags'))
        self.assertEqual(len(note1.book.selected_tags), 0)
        self.assertEqual(note2.book, None)

    def test_tags(self):
        tags = []
        for i in range(100):
            tags.append(Tag.objects.create(name="Tag %s" % i))
        author = Author.objects.create(name="Johnny")
        book = Book.objects.create(name="TaggedBook", author=author)
        book.tags.add(*tags[::7])

        for i in Book.objects.prefetch('tags').filter(pk=book.pk):
            self.assertTrue(hasattr(i, 'prefetched_tags'))
            self.assertEqual(len(i.selected_tags), 15, i)
            self.assertEqual(set(i.selected_tags), set(tags[::7]), i)

        for i in Book.objects.filter(pk=book.pk):
            self.assertFalse(hasattr(i, 'prefetched_tags'))
            self.assertEqual(len(i.selected_tags), 15, i)
            self.assertEqual(set(i.selected_tags), set(tags[::7]), i)

    def test_books_queryset_get(self):
        author = Author.objects.create(name="John Doe")
        for i in range(3):
            Book.objects.create(name="Book %s" % i, author=author)

        i = Author.objects.prefetch('books').get(pk=author.pk)
        self.assertTrue(hasattr(i, 'prefetched_books'))
        self.assertEqual(len(i.books), 3, i.books)

        i = Author.objects.get(name="John Doe")
        self.assertFalse(hasattr(i, 'prefetched_books'))
        self.assertEqual(len(i.books), 3, i.books)

    def test_using_db(self):
        author = Author.objects.using('secondary').create(name="John Doe")
        for i in range(3):
            Book.objects.using('secondary').create(name="Book %s" % i, author=author)

        for i in Author.objects.prefetch('books').filter(pk=author.pk).using('secondary'):
            self.assertTrue(hasattr(i, 'prefetched_books'))
            self.assertEqual(len(i.books), 3, i.books)

        for i in Author.objects.using('secondary').prefetch('books').filter(pk=author.pk):
            self.assertTrue(hasattr(i, 'prefetched_books'))
            self.assertEqual(len(i.books), 3, i.books)

        for i in Author.objects.db_manager('secondary').prefetch('books').filter(pk=author.pk):
            self.assertTrue(hasattr(i, 'prefetched_books'))
            self.assertEqual(len(i.books), 3, i.books)

        for i in Author.objects.filter(pk=author.pk).using('secondary'):
            self.assertFalse(hasattr(i, 'prefetched_books'))
            self.assertEqual(len(i.books), 3, i.books)

    def test_wrong_prefetch_subclass_and_instance(self):
        with self.assertRaises(InvalidPrefetch) as cm:
            PrefetchManager(
                latest_book_as_instance=LatestBook(),
            )

        self.assertEqual(cm.exception.args, (
            "Invalid prefetch definition latest_book_as_instance. This prefetcher needs to be a class not an "
            "instance.",))

    def test_wrong_prefetch_options_and_simple_prefetch(self):
        with self.assertRaises(InvalidPrefetch) as cm:
            Author.objects.prefetch(P('latest_book'))
        self.assertEqual(1, len(cm.exception.args))
        self.assertRegexpMatches(cm.exception.args[0],
                                 r"Invalid prefetch call with latest_book for on model <class "
                                 r"'test_app\.models\.Author'>. This prefetcher \(<prefetch\.Prefetcher object at "
                                 r"0x\w+>\) needs to be a subclass of Prefetcher\.")

    def test_wrong_prefetch_fwd(self):
        with self.assertRaises(InvalidPrefetch) as cm:
            Book.objects.prefetch('author__asdf')

        self.assertEqual(cm.exception.args, (
            "Invalid part asdf in prefetch call for author__asdf on model <class 'test_app.models.Book'>. The name is "
            "not a prefetcher nor a forward relation (fk).",))

    def test_wrong_prefetch_after_miss(self):
        with self.assertRaises(InvalidPrefetch) as cm:
            Book.objects.prefetch('author')

        self.assertEqual(cm.exception.args, (
            "Invalid prefetch call with author for on model <class 'test_app.models.Book'>. The last part isn't a "
            "prefetch definition.",))

    def test_wrong_prefetch_after_wrong(self):
        with self.assertRaises(InvalidPrefetch) as cm:
            Author.objects.prefetch('books__asdf')

        self.assertEqual(cm.exception.args, (
            "Invalid part asdf in prefetch call for books__asdf on model <class 'test_app.models.Author'>. You cannot "
            "have any more relations after the prefetcher.",))

    def test_wrong_prefetch_fwd_no_manager(self):
        with self.assertRaises(InvalidPrefetch) as cm:
            Book.objects.prefetch('publisher__whatev')

        self.assertEqual(cm.exception.args,
                         ("Manager for <class 'test_app.models.Publisher'> is not a PrefetchManagerMixin instance.",))

    def test_wrong_prefetch(self):
        with self.assertRaises(InvalidPrefetch) as cm:
            Author.objects.prefetch('asdf')

        self.assertEqual(cm.exception.args, (
            "Invalid part asdf in prefetch call for asdf on model <class 'test_app.models.Author'>. The name is not a "
            "prefetcher nor a forward relation (fk).",))

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
        Author.objects.create(name="John Doe")

        asserting_handler = AssertingHandler(10)
        logging.getLogger().addHandler(asserting_handler)

        self.assertRaises(SillyException, lambda: list(Author.objects.prefetch('silly')))

        asserting_handler.assertLogged(self,
                                       "Prefetch failed for silly prefetch on the Author model:\nTraceback (most "
                                       "recent call last):")
        logging.getLogger().removeHandler(asserting_handler)

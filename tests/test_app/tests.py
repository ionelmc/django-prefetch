from django.test import TestCase

from models import Book, Author

class PrefetchTests(TestCase):
    def test_books(self):
        author = Author.objects.create(name="John Doe")
        for i in range(3):
            Book.objects.create(name="Book %s"%i, author=author)

        for i in Author.objects.prefetch('books'):
            self.assertTrue(hasattr(i, 'prefetched_books'))
            self.assertEquals(len(i.books), 3, i.books) 

        for i in Author.objects.all():
            self.assertFalse(hasattr(i, 'prefetched_books'))
            self.assertEquals(len(i.books), 3, i.books) 
    
    #def test_books_get(self):
    #    i = Author.objects.prefetch('books').get(name="John Doe")
    #    self.assertTrue(hasattr(i, 'prefetched_books'))
    #    self.assertEquals(len(i.books), 3, i.books) 
    #
    #    i = Author.objects.get(name="John Doe")
    #    self.assertFalse(hasattr(i, 'prefetched_books'))
    #    self.assertEquals(len(i.books), 3, i.books) 

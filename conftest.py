try:
    from django import setup
except ImportError:
    pass
else:
    def pytest_configure():
        setup()
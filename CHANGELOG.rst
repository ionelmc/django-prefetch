
Changelog
=========

1.2.1 (2018-09-04)
------------------

* Fixed missing entry in changelog.

1.2.0 (2018-09-04)
------------------

* Added support for Django 1.11, dropped support for Django <1.9. Contributed by Martin Bachwerk in
  `#16 <https://github.com/ionelmc/django-prefetch/pull/16>`_.

1.1.0 (2016-02-20)
------------------

* Fixed a test assertion. Contributed by George Ma in `#12 <https://github.com/ionelmc/django-prefetch/pull/12>`_.
* Added support for Django 1.9. Contributed by Will Stott in `#14 <https://github.com/ionelmc/django-prefetch/pull/14>`_.
* Fixed use of deprecated `field.rel.to` momdel API (Django 1.9+).

1.0.1 (2015-09-05)
------------------

* Fixed manager type check. Contributed by George Ma in `#11 <https://github.com/ionelmc/django-prefetch/issues/11>`_.

1.0.0 (2014-12-05)
------------------

* Fixed issues with ``select_related`` being removed when prefetch is used (`#9 <https://github.com/ionelmc/django-prefetch/issues/9>`_).

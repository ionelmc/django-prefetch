from logging import getLogger
logger = getLogger(__name__)

import time
import collections

from django.db import models
from django.db.models import query
from django.db.models.fields.related import ReverseSingleRelatedObjectDescriptor

class FakePrefetchManager(models.Manager):
    def __init__(self, **kws):
        super(FakePrefetchManager, self).__init__()

    def get_query_set(self):
        qs = FakePrefetchQuerySet(self.model)
        if getattr(self, '_db', None) is not None:
            qs = qs.using(self._db)
        return qs

    def prefetch(self, *args):
        return self.get_query_set()

class FakePrefetchQuerySet(query.QuerySet):
    def prefetch(self, *args):
        return self


FakePrefetchManager.use_for_related_fields = True

class PrefetchManager(models.Manager):
    def __init__(self, **kwargs):
        super(PrefetchManager, self).__init__()
        self.prefetch_definitions = kwargs
        for name in kwargs:
            kwargs[name].name = name

    def get_query_set(self):
        qs = PrefetchQuerySet(self.model)
        if getattr(self, '_db', None) is not None:
            qs = qs.using(self._db)
        return qs

    def prefetch(self, *args):
        return self.get_query_set().prefetch(*args)

PrefetchManager.use_for_related_fields = True

class InvalidPrefetch(Exception):
    pass

class PrefetchQuerySet(query.QuerySet):
    def __init__(self, model=None, query=None, using=None):
        if using is None: # this is to support Django 1.1
            super(PrefetchQuerySet, self).__init__(model, query)
        else:
            super(PrefetchQuerySet, self).__init__(model, query, using)
        self._prefetch = {}

    def _clone(self, klass=None, setup=False, **kwargs):
        return super(PrefetchQuerySet, self)._clone(klass, setup, _prefetch=self._prefetch, **kwargs)

    def prefetch(self, *names):
        obj = self._clone()

        for name in names:
            parts = name.split('__')
            forwarders = []
            prefetcher = None
            model = self.model

            for what in parts:
                if not prefetcher:
                    assert isinstance(model.objects, PrefetchManager), 'Manager for %s is not a PrefetchManager instance.' % model

                    if what in model.objects.prefetch_definitions:
                        prefetcher = model.objects.prefetch_definitions[what]
                        continue
                    descriptor = getattr(model, what, None)
                    if isinstance(descriptor, ReverseSingleRelatedObjectDescriptor):
                        forwarders.append(descriptor.field.name)
                        model = descriptor.field.rel.to
                    else:
                        raise InvalidPrefetch("Invalid part %s in prefetch call for %s on model %s. The name is not a prefetcher nor a forward relation (fk)." % (what, name, self.model))
                else:
                    raise InvalidPrefetch("Invalid part %s in prefetch call for %s on model %s. You cannot have any more relations after the prefetcher." % (what, name, self.model))
            if not prefetcher:
                raise InvalidPrefetch("Invalid prefetch call with %s for on model %s. The last part isn't a prefetch definition." % (name, self.model))
            obj._prefetch[name] = forwarders, prefetcher
        for forwarders, prefetcher in obj._prefetch.values():
            if forwarders:
                obj = obj.select_related('__'.join(forwarders))
        return obj

    def iterator(self):
        data = list(super(PrefetchQuerySet, self).iterator())
        for name, (forwarders, prefetcher) in self._prefetch.iteritems():
            prefetcher.fetch(data, name, self.model, forwarders,
                             getattr(self, '_db', None))
        return iter(data)

class Prefetcher(object):
    """
    Prefetch definitition. For convenience you can either subclass this and define the methods on the subclass or just pass the functions to the contructor. 
    
    Eg, subclassing::
    
        class GroupPrefetcher(Prefetcher):
            
            @staticmethod
            def filter(ids):
                return User.groups.through.objects.filter(user__in=ids).select_related('group')
            
            @staticmethod
            def reverse_mapper(user_group_association):
                return [user_group_association.user_id]

            @staticmethod
            def decorator(user, user_group_associations=()):
                setattr(user, 'prefetched_groups', [i.group for i in user_group_associations])
        
    Or with contructor::

        Prefetcher(
            filter = lambda ids: User.groups.through.objects.filter(user__in=ids).select_related('group'),
            reverse_mapper = lambda user_group_association: [user_group_association.user_id],
            decorator = lambda user, user_group_associations=(): setattr(user, 'prefetched_groups', [i.group for i in user_group_associations])
        )

    
    Glossary:
    
    * filter: 
        
        A function that returns a iterable containing related data for a given list of keys.
        
    * reverse_mapper:
    
        A function that takes the related object as argument and returns a list of keys that maps that related object to the objects in the queryset. 
            
    * mapper:
        
        Optional (defaults to ``lambda obj: obj.id``). 
        
        A function that returns the key for a given object in your query set.
        
    * decorator:
    
        A function that will save the related data on each of your objects. Takes the object and a list of related objects as arguments.
    
    """
    
    def __init__(self, filter=None, reverse_mapper=None, decorator=None, mapper=None, collect=False):
        if filter:
            self.filter = filter
        else:
            assert hasattr(self, 'filter'), "You must define a filter function"
        
        if reverse_mapper:
            self.reverse_mapper = reverse_mapper
        else:
            assert hasattr(self, 'reverse_mapper'), "You must define a reverse_mapper function"
            
        if decorator:
            self.decorator = decorator
        else:
            assert hasattr(self, 'decorator'), "You must define a decorator function"

        if mapper:
            self.mapper = mapper
            
        self.collect = collect
    
    @staticmethod
    def mapper(obj):
        return obj.id
        
    def fetch(self, dataset, name, model, forwarders, db):
        if forwarders:
            self.collect = True
        try:
            data_mapping = collections.defaultdict(list)
            t1 = time.time()
            for obj in dataset:
                for field in forwarders:
                    obj = getattr(obj, field, None)

                if not obj:
                    continue

                if self.collect:
                    data_mapping[self.mapper(obj)].append(obj)
                else:
                    data_mapping[self.mapper(obj)] = obj

                self.decorator(obj)

            t2 = time.time()
            logger.debug("Creating data_mapping for %s query took %.3f secs for the %s prefetcher.", model.__name__, t2-t1, name)
            t1 = time.time()
            related_data = self.filter(data_mapping.keys())
            if db is not None:
                related_data = related_data.using(db)
            related_data_len = len(related_data)
            t2 = time.time()
            logger.debug("Filtering for %s related objects for %s query took %.3f secs for the %s prefetcher.", related_data_len, model.__name__, t2-t1, name)
            relation_mapping = collections.defaultdict(list)

            t1 = time.time()
            for obj in related_data:
                for id_ in self.reverse_mapper(obj):
                    if id_:
                        relation_mapping[id_].append(obj)
            for id_, related_items in relation_mapping.items():
                if id_ in data_mapping:
                    if self.collect:
                        for item in data_mapping[id_]:
                            self.decorator(item, related_items)
                    else:
                        self.decorator(data_mapping[id_], related_items)

            t2 = time.time()
            logger.debug("Adding the related objects on the %s query took %.3f secs for the %s prefetcher.", model.__name__, t2-t1, name)
            return dataset
        except:
            logger.exception("Prefetch failed for %s prefetch on the %s model:", name, model.__name__)
            raise

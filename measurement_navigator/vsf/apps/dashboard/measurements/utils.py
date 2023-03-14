"""
Utility functions and classes used in measurement and submeasurement views
"""

# Django imports
from django.db.models  import QuerySet
from django.core.cache import caches

# Local imports
from vsf.views import VSFLoginRequiredMixin
from vsf.utils import Colors as c
import hashlib

# Third party imports
from django_datatables_view.base_datatable_view import BaseDatatableView

# Python imports
from typing import List, Dict, Any

class VSFCachedDatatableView(VSFLoginRequiredMixin, BaseDatatableView):
    """
        This is a base view class to implement cache for datatables information. 
        To implement this class, you just need to implement `prepare_results_no_cache`,
        this is what you would normally implement in `prepare_results`. If you want to 
        override caching or implement a specific way of caching, you can override `prepare_results`
    """
    
    # how many seconds cache will live before it is deleted
    SECONDS_TO_STORE_CACHE = 60 * 5

    def prepare_results_no_cache(self, qs : QuerySet) -> List[Dict[str, Any]]:
        raise NotImplementedError("Implement prepare_results_no_cache in your submeasurement backend view in order to fill the datatables table")

    def prepare_results(self, qs : QuerySet, cache_adjacent_pages : bool = False) -> List[Dict[str, Any]]:
        """Don't override this unless you want to prevent query caching. This function will search for a cached result of the provided query. you 
        can do:
            ```
            def prepare_results(self, qs):
                self.prepare_results_no_cache(qs)
            ```
        in case you want to avoid caching for this view

        Args:
            qs (QuerySet): Queryset whose result will be cached

        Returns:
            List[Dict[str, Any]]: Prepared results as a list of json-like dicts
        """
        key = self._get_key_from_query(qs)
        fs_cache = caches['filesystem']

        # try to retrieve key from cache
        if key in fs_cache:
            print(c.green("Cache found, using cache"))
            result = fs_cache.get(key)
        else: 
            # If not found, then create it 
            print(c.blue("Cache not found, creating from scratch"))
            result = self.prepare_results_no_cache(qs)
            fs_cache.set(key, result, self.SECONDS_TO_STORE_CACHE)

        return result

    def _get_key_from_query(self, qs : QuerySet) -> str:
        """Generate a sha256 key from a given queryset, so it can be used to cache results for a few minutes

        Args:
            qs (QuerySet): Query in database to cache

        Returns:
            str: sha256 hash for the given query
        """
        query_str = str(qs.query)
        query_hash = hashlib.sha256(bytes(query_str, 'utf-8')).digest()
        return str(query_hash)

    def count_records(self, qs : QuerySet):
        # Overriden to provide caching to this view

        key = self._get_key_from_query(qs)
        key = "count_" + key
        fs_cache = caches['filesystem']
        if key in fs_cache:
            return fs_cache.get(key)
        
        result = super().count_records(qs)
        fs_cache.set(key, result, self.SECONDS_TO_STORE_CACHE)

        return result 

    @staticmethod
    def _generate_sql_querys_for_adjacent_pages(qs : QuerySet, num_adjacent_pages : int = 5) -> List[str]:
        """Generate SQL query strings for the next and previous adjacent pages

        Args:
            qs (QuerySet): queryset containing limit and (optionally) offset to generate more querys from. 
            num_adjacent_pages (int): How many pages before and after the one specified by qs to take. For example, 
            if qs contains page 10 and num_adjacent_pages == 5, then you will get SQL querys for pages 5 to 15, excluding 10.
        Return:
            List of querys as strings. Might be less if some pages makes no sense, like requesting the previous 5 pages of page 0
        """
        original_sql_str = str(qs.query)
        assert  "LIMIT" in original_sql_str, "Can't generate previous pages without page size"
        original_sql_str_words = original_sql_str.split()

        # Search index of "Limit" keyword in array
        limit_i = original_sql_str_words.index("LIMIT")
        
        # Do the same for OFFSET, but if not present assume it's 0:
        try: 
            offset_i = original_sql_str_words.index("OFFSET")
        except ValueError:
            offset_i = -1
        
        # Parse limit
        limit = int(original_sql_str_words[limit_i + 1]) 
        offset = int(original_sql_str_words[offset_i + 1]) if offset_i != -1 else 0

        # Get actual page number
        page_num = offset // limit

        # Itarate over pages to build.
        sql_querys = []

        if offset_i == -1:
            offset_i = len(original_sql_str_words)
            original_sql_str_words.extend(["OFFSET", "0"])

        for i in range(page_num - num_adjacent_pages, page_num + num_adjacent_pages + 1):

            # Skip if in an invalid page
            if i < 0 or i == page_num:
                continue
            
            original_sql_str_words[offset_i + 1] = str(limit * i)
            sql_querys.append(" ".join(original_sql_str_words))
        
        return sql_querys
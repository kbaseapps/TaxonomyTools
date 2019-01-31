import json
import logging
from pprint import pformat
from functools import lru_cache

import requests


class RE_API:
    def __init__(self, re_url, token):
        self.re_url = re_url
        self.token = token

    def _call_re(self, endpoint="/api/query_results/", params=None, data=None):
        header = {"Authorization": self.token}
        ret = requests.post(self.re_url+endpoint, data, params=params, headers=header)
        return ret.json()

    @lru_cache(256)
    def get_referred_counts_by_type(self, ws_ref, is_private=False, is_public=False, owners=(),
                                    simplify_type=True):
        if len(owners) < 1:
            owners = False
        
        body = json.dumps({'key':            ws_ref.replace('/', ':'),
                           'is_private':     is_private,
                           'is_public':      is_public,
                           'owners':         owners,
                           'simplify_type':  simplify_type
                           })
        ret = self._call_re(params={'view': "list_referencing_type_counts"}, data=body)
        if "error" in ret:
            raise RuntimeError(f"{ret['error']}: {ret.get('arango_message', '')}")

        return ret['results']

import json
import logging
from pprint import pformat
from functools import lru_cache

import requests


class RE_API:
    def __init__(self, re_url, token):
        self.re_url = re_url
        self.token = token

    def _call_re(self, endpoint="/api/v1/query_results/", params=None, data=None):
        header = {"Authorization": self.token}
        ret = requests.post(self.re_url+endpoint, data, params=params, headers=header)
        return ret.json()

    @lru_cache(256)
    def wsprov_list_referencing_type_counts(self, ws_ref, show_private=False, show_public=False,
                                            owners=(), simplify_type=True):
        if len(owners) < 1:
            owners = False
        
        body = json.dumps({'key':            ws_ref.replace('/', ':'),
                           'show_private':     show_private,
                           'show_public':      show_public,
                           'owners':         owners,
                           'simplify_type':  simplify_type
                           })
        ret = self._call_re(params={'view': "wsprov_list_referencing_type_counts"}, data=body)
        if "error" in ret:
            raise RuntimeError(f"{ret['error']}: {ret.get('arango_message', '')}")

        return ret['results'][0]

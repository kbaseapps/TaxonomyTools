import json
import logging
from pprint import pformat

import requests


class RE_API:
    def __init__(self, re_url, token):
        self.re_url = re_url
        self.token = token

    def _call_re(self, endpoint="/api/query_results/", params=None, data=None):
        header = {"Authorization": self.token}
        logging.info(f"Calling RE_API with query data: {pformat(data)}")
        ret = requests.post(self.re_url+endpoint, data, params=params, headers=header)
        return ret.json()


    def get_referred_counts_by_type(self, ws_ref, is_private=False, is_public=False, owners=[],
                                         simplify_type=True ):

        if not isinstance( owners, list ):
            raise RuntimeError( f"parameter 'owners' not a list: {owners}" )
        # maybe ensure each element of owners is type 'str'?

        if len( owners ) < 1:
            owners = False
        
        body = json.dumps({'key':            ws_ref.replace( '/', ':'),
                           'is_private':     is_private,
                           'is_public':      is_public,
                           'owners':         owners,
                           'simplify_type':  simplify_type
                          })
        logging.info( "############## json body {0}".format( pformat( body ) ) )
        ret = self._call_re(params={'view': "list_referencing_type_counts"}, data=body)
        #ret = []
        if "error" in ret:
            raise RuntimeError(f"{ret['error']}: {ret.get('arango_message', '')}")
        #logging.info(f"Found {ret['results'][0]['count']} related sequences")
        logging.info( "########### Arango query return {0}".format( pformat( ret ) ) )

        return ret

        #return ret['results'][0]['sequences']


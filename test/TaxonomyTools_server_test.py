# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser

from TaxonomyTools.TaxonomyToolsImpl import TaxonomyTools
from TaxonomyTools.TaxonomyToolsServer import MethodContext
from TaxonomyTools.authclient import KBaseAuth as _KBaseAuth

from installed_clients.WorkspaceClient import Workspace
from installed_clients.GenericsAPIClient import GenericsAPI


class TaxonomyToolsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = os.environ.get('KB_AUTH_TOKEN', None)
        config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('TaxonomyTools'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'TaxonomyTools',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = Workspace(cls.wsURL)
        cls.serviceImpl = TaxonomyTools(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']
        suffix = int(time.time() * 1000)
        cls.wsName = "test_ContigFilter_" + str(suffix)
        ret = cls.wsClient.create_workspace({'workspace': cls.wsName})  # noqa

        cls.gapi = GenericsAPI(cls.callback_url)
        params = {'obj_type': 'AmpliconMatrix',
                  'matrix_name': 'test_AmpliconMatrix',
                  'workspace_name': cls.wsName,
                  "tsv": {
                      "tsv_file_tsv": os.path.join('data', 'amplicon_test.tsv'),
                      'metadata_keys_tsv': 'taxonomy_id, taxonomy, taxonomy_source, consensus_sequence'
                  },
                  'scale': 'raw',
                  'description': "OTU data",
                  'amplicon_set_name': 'test_AmpliconSet'
                  }
        ret = cls.gapi.import_matrix_from_biom(params)[0]
        cls.amplicon_set_ref = ret['amplicon_set_obj_ref']

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    def integration_test(self):
        ret = self.serviceImpl.objects_counts_by_taxon(self.ctx, {'workspace_name': self.wsName,
                                                                  'taxa_ref': self.amplicon_set_ref,
                                                                  'data_source': 'search'
                                                                  })[0]
        self.assertCountEqual(ret.keys(), ['report_name', 'report_ref', 'object_counts'])

    def bad_input_test(self):
        with self.assertRaisesRegex(ValueError, "Required keys"):
            self.serviceImpl.objects_counts_by_taxon(self.ctx, {'taxa_ref': self.amplicon_set_ref,
                                                                'data_source': 'search'
                                                                })
        with self.assertRaisesRegex(ValueError, "Required keys"):
            self.serviceImpl.objects_counts_by_taxon(self.ctx, {'workspace_name': self.wsName,
                                                                'data_source': 'search'
                                                                })
        with self.assertRaisesRegex(ValueError, "Required keys"):
            self.serviceImpl.objects_counts_by_taxon(self.ctx, {'workspace_name': self.wsName,
                                                                'taxa_ref': self.amplicon_set_ref,
                                                                })
        with self.assertRaisesRegex(ValueError, 'Invalid value for "data_source"'):
            self.serviceImpl.objects_counts_by_taxon(self.ctx, {'workspace_name': self.wsName,
                                                                'taxa_ref': self.amplicon_set_ref,
                                                                'data_source': 'search'
                                                                })

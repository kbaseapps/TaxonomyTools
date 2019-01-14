# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os

from TaxonomyTools.core.app_impl import AppImpl
#END_HEADER


class TaxonomyTools:
    '''
    Module Name:
    TaxonomyTools

    Module Description:
    A KBase module: TaxonomyTools
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = ""
    GIT_COMMIT_HASH = ""

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.shared_folder = config['scratch']
        self.config = config
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)
        #END_CONSTRUCTOR
        pass


    def objects_counts_by_taxon(self, ctx, params):
        """
        Get a listing of workspace objects that relate that match taxa in a set separated by type.
        Returns results in a KBaseReport
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN objects_counts_by_taxon
        app_impl = AppImpl(self.config, ctx)
        output = app_impl.objects_counts_by_taxon(params)
        #END objects_counts_by_taxon

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method objects_counts_by_taxon return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]

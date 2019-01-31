import logging
import os
import uuid
from functools import lru_cache

from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.KBaseSearchEngineClient import KBaseSearchEngine
from TaxonomyTools.core.re_api import RE_API

from pprint import pformat

class AppImpl:
    @staticmethod
    def _validate_params(params, required, optional=set()):
        """Validates that required parameters are present. Warns if unexpected parameters appear"""
        required = set(required)
        optional = set(optional)
        pkeys = set(params)
        if required - pkeys:
            raise ValueError("Required keys {} not in supplied parameters"
                             .format(", ".join(required - pkeys)))
        defined_param = required | optional
        for param in params:
            if param not in defined_param:
                logging.warning("Unexpected parameter {} supplied".format(param))

    def _get_taxa(self, params):
        data = self.dfu.get_objects(
            {'object_refs': [params['taxa_ref']]}
        )['data'][0]['data']
        logging.info(data)
        taxa = [{'id': amp_id,
                 'name': amp['taxonomy'].get('scientific_name'),
                 'ref': amp['taxonomy'].get('taxonomy_ref')}
                for amp_id, amp in data['amplicons'].items()]
        return taxa

    def _get_counts_from_search(self, taxon_list):
        counts = {}
        for taxon in taxon_list:
            if not taxon.get('name'):
                counts[taxon['id']] = {}
                continue
            ret = self._search_taxon(taxon.get('name'))
            counts[taxon['id']] = ret['type_to_count']

        return counts

    @lru_cache(256)
    def _search_taxon(self, taxon_name):
        search_params = {
            "match_filter": {
                "full_text_in_all": taxon_name,
                "exclude_subobjects": 1,
            },
            "access_filter": {
                "with_private": 1,
                "with_public": 1
            }
        }
        ret = self.kbse.search_types(search_params)
        logging.info(ret)
        return ret

    def _get_counts_from_ke(self, params, taxon_list):
        counts = {}
        for taxon in taxon_list:
            _id, name, ref = [taxon.get(x) for x in ["id", "name", "ref"]]
            logging.info(f'###### taxon {_id} {name} {ref}')
            ret = self.re_api.get_referred_counts_by_type(ref)
            counts[_id] = {obj['type']: obj['type_count'] for obj in ret}

        return counts
        
    def _build_report(self, taxon_list, object_counts, workspace_name):
        """
        _generate_report: generate summary report with counts
        """
        output_html_files = self._generate_report_html(taxon_list, object_counts)

        report_params = {
            'html_links': output_html_files,
            'direct_html_link_index': 0,
            'workspace_name': workspace_name,
            'report_object_name': f'objects_counts_by_taxon_{uuid.uuid4()}'}

        output = self.kbr.create_extended_report(report_params)

        return {'report_name': output['name'], 'report_ref': output['ref']}

    def _generate_report_html(self, taxon_list, object_counts):
        """
            _generate_report: generates the HTML for the upload report
        """
        html_report = list()

        # Make report directory and copy over files
        output_directory = os.path.join(self.scratch, str(uuid.uuid4()))
        os.mkdir(output_directory)
        result_file_path = os.path.join(output_directory, 'find_genes_for_rxn.html')

        # Build HTML tables for results
        table_lines = []
        table_lines.append(f'<h3 style="text-align: center">Object Counts</h3>')
        table_lines.append('<table class="table table-bordered table-striped">')
        header = "</td><td>".join(['Amplicon', 'Taxon'] + self.object_categories)
        table_lines.append(f'\t<thead><tr><td>{header}</td></tr></thead>')
        table_lines.append('\t<tbody>')
        for taxon in taxon_list:
            row = [taxon['id'], taxon['name']]
            row += [str(object_counts[taxon['id']].get(ws_type, 0))
                    for ws_type in self.object_categories]
            line = "</td><td>".join(row)
            table_lines.append(f'\t\t<tr><td>{line}</td></tr>')
        table_lines.append('\t</tbody>')
        table_lines.append('</table>\n')

        # Fill in template HTML
        with open(os.path.join(os.path.dirname(__file__), 'table_report_template.html')
                  ) as report_template_file:
            report_template = report_template_file.read() \
                .replace('*TABLES*', "\n".join(table_lines))

        with open(result_file_path, 'w') as result_file:
            result_file.write(report_template)

        html_report.append({'path': output_directory,
                            'name': os.path.basename(result_file_path),
                            'description': 'HTML report for objects_counts_by_taxon app'})

        return html_report

    def __init__(self, config, ctx):
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.scratch = config['scratch']
        self.re_api = RE_API(config['re-url'], ctx['token'])
        self.dfu = DataFileUtil(self.callback_url)
        self.kbse = KBaseSearchEngine(config['search-url'])
        self.kbr = KBaseReport(self.callback_url)
        self.object_categories = ['Narrative', 'Assembly', 'Genome', 'FBAModel', 'Tree']

    def objects_counts_by_taxon(self, params):
        self._validate_params(params, {'workspace_name', 'taxa_ref', 'data_source', })
        taxa = self._get_taxa(params)

        if params['data_source'] == 'search':
            counts = self._get_counts_from_search(taxa)
        elif params['data_source'] == 're':
            counts = self._get_counts_from_ke(params, taxa)
        else:
            raise ValueError(f'Invalid value for "data_source": {params["data_source"]}')

        output = {'object_counts': counts}
        output.update(self._build_report(taxa, counts, params['workspace_name']))
        return output



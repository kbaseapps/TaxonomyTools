import logging
import os
import uuid

from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.KBaseSearchEngineClient import KBaseSearchEngine
from TaxonomyTools.core.re_api import RE_API


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
        return [{"name": "foo"}, {"name": "foo"}]

    def _get_counts_from_search(self, params, taxon_list):
        return {
            "foo": {"Narrative": 1, "Genome": 35},
            "bar": {"Genome": 21, "ExpressionMatrix": 32}
            }

    def _get_counts_from_ke(self, params, taxon_list):
        raise NotImplementedError

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
        header = "</td><td>".join(['Taxon'] + self.object_categories)
        table_lines.append(f'\t<thead><tr><td>{header}</td></tr></thead>')
        table_lines.append('\t<tbody>')
        for taxon in taxon_list:

            row = [taxon['name']] + [object_counts[taxon['name']].get(ws_type, 0)
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
        self.kbse = KBaseSearchEngine(config['search-url'])
        self.kbr = KBaseReport(self.callback_url)
        self.object_categories = ['Narrative', 'Genome', 'ExpressionMatrix']

    def objects_counts_by_taxon(self, params):
        self._validate_params(params, {'workspace_name', 'taxa_ref', 'data_source', })
        taxa = self._get_taxa(params)

        if params['data_source'] == 'search':
            counts = self._get_counts_from_search(params, taxa)
        elif params['data_source'] == 're':
            counts = self._get_counts_from_ke(params, taxa)
        else:
            raise ValueError(f'Invalid value for "data_source": {params["data_source"]}')

        output = {'object_counts': counts}
        output.update(self._build_report(params['taxons'],
                                         counts,
                                         params['workspace_name'],
                                         ))
        return output



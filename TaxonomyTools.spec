/*
A KBase module: TaxonomyTools
*/

module TaxonomyTools {
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    /*
        Get a listing of workspace objects that relate that match taxa in a set separated by type.
        Returns results in a KBaseReport
    */
    funcdef objects_counts_by_taxon(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

};

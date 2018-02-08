#!/usr/bin/env python3

"""es_tools.py:  A script to rename Newman label ID's within Elasticsearch."""
__author__      = "Robert Parkhurst"
__version__     = "1.0.1"
__email__       = "robert.parkhurst@keywcorp.com"
__maintainer__  = "Robert Parkhurst"


import optparse
import sys
import pprint


try:
    import requests
except Exception as ex:
    print("Error importing requests")
    sys.exit(1)

try:
    import elasticsearch

    es_version_tuple = elasticsearch.__version__
    if(es_version_tuple[0] < 2 or es_version_tuple[0] > 2):
        print("Error:  Elasticsearch pip module is not running a supported version!  Only 2.x is supported at this time")
        print("Please run pip2 install -r ./requirements/requirements_es_index_rename.txt")
        sys.exit(1)

except Exception as ex:
    print("Error:  Unable to import elasticsearch module.")
    print("Please run pip2 install -r ./requirements/requirements_es_index_rename.txt")
    sys.exit(1)



parser = optparse.OptionParser()
parser.add_option('--verbose',
                  help="enable verbose reporting",
                  action="store_true",
                  default=False,
                  dest="verbose")

parser.add_option('--version',
                  help="display version information",
                  action="store_true",
                  default=False,
                  dest="version")

parser.add_option("--esCluster",
                  help="Name of Elastic Search Cluster.  Defaults to `localhost` if not provided.",
                  dest="es_cluster",
                  default="localhost")

parser.add_option("--list",
                  help="list Elasticsearch indicies and the corresponding Newman Web UI labels (probably run this first)",
                  action="store_true",
                  dest="es_ls",
                  default=False)

parser.add_option("--changeLabel",
                  help="Change label of an index.  MUST BE USED with esCluster AND esIndex.  Use quotes when providing a name.  Example:  --label \"New Newman Label\"",
                  dest="es_label")

parser.add_option("--esIndex",
                  help="ES Index to change Newman Label of.  Must be used with --label.  Use --ls to get a list of newman indices and their corresponding web ui labels.",
                  dest="es_index")

parser.add_option("--deleteStatsIndex",
                  help="Delete the dataset statistics ES index to allow for re-indexing to occur on next web UI refresh",
                  dest="deleteDatasetIndex",
                  default=False)



options, remainder = parser.parse_args()
parser.parse_args()
pp = pprint.PrettyPrinter(indent=4)


def ls_indices():
    """
    Function to list Elasticsearch indices
    Can help to identify what underlying newman-XXXXX index maps to what Newman web UI label

    :return: nothing
    """
    print("Index => Newman Label Map:")
    for idx in es.indices.get('*'):
        try:
            res = es.search(index=idx, body={"query":{"bool":{"must":[{"query_string":{"default_field":"_all","query":idx}}],"must_not":[],"should":[]}},"from":0,"size":1,"sort":[],"aggs":{}})
            label = res['hits']['hits'][0]['_source']['label']
        except Exception as ex:
            label = "nil"
            continue
        print("\t" + idx + "\t=>\t" + label)
def es_label_update(es_index, label_name):
    """
    Function to update an Elasticsearch label for newman.  This *ONLY* affects the newman web ui front end.

    :param es_index:
    :param label_name:
    :return: nothing
    """

    try:
        es.update(index=es_index,

                  doc_type=es_index,
                  id=es_index,
                  body={"doc": { "label": label_name}})
    except Exception as ex:
        print("Error:  Unable to update Elasticsearch index label.  Please verify that this ES index is a newman index.")
        print(ex)
def es_delete_dataset_index():
    """
    Function to drop the dataset statistics index
    :return:
    """

    if(options.verbose):
        print("Droping ES Dataset statistics index")

    try:
        es.indices.delete(index='dataset_stats')
    except Exception as ex:
        print("Error deleting dataset stats -- make sure it exists and you have permission to do so!")
        print(ex)

    if(options.verbose):
        print("dataset_stats index should now be deleted!  Please check your ES cluster to verify")
def print_version_info():
    """
    simple function to print version information.  This is a weak version output and as such it is not indicitive
    of all changes made/not made to this code, but should be seen as a general/rough idea.
    :return:
    """
    print("version is:  " + __version__)
    print("Elasticsearch pip module version is:  " + get_es_module_version())
def get_es_module_version():
    """
    Function to format the version information returned from the elasticsearch module into a string
    :return:
    """
    es_version = ''
    for i in elasticsearch.__version__:
        es_version += str(i)
        es_version += "."

    es_version = es_version[:-1]

    return es_version



if __name__ == "__main__":
    if (options.verbose):
        print("verbose is:  " + str(options.verbose))
        print("Elasticsearch module is:  " + str(elasticsearch.__version__))


    # if we get the request for version information, display that then quit -- no need to go on
    if (options.version):
        print_version_info()
        sys.exit(0)


    # Try to make a connection to elasticsearch
    # If elasticsearch wasn't specified it defaults to 'localhost'
    try:
        res = requests.get("http://" + options.es_cluster + ":9200")
        es = elasticsearch.Elasticsearch([{'host': options.es_cluster, 'port': '9200'}])

        if(options.verbose):
            print("request (res) content is:  ")
            pp.pprint(res.content)

            print("elasticsearch connection made!")
            print(str(es))
    except Exception as ex:
        print("Error:  Unable to connect to elasticsearch cluster!")
        print(ex)
        sys.exit(0)


    # if we want to do an 'ls' on the cluster
    if (options.es_ls):
        ls_indices()

    # if we want to rename a label
    elif (options.es_label is not None or options.es_index is not None):
        if (options.es_index is None):
            print("Error:  No elasticsearch index id specified!")
            sys.exit(0)
        if (options.es_label is None):
            print("Error:  Label is not specified")
            sys.exit(0)

        if (options.verbose):
            print("ES Cluster:  " + str(options.es_cluster))
            print("ES Index:  " + str(options.es_index))
            print("ES Label:  " + str(options.es_label))
        try:
            es_label_update(es_index=options.es_index, label_name=options.es_label)
            es_delete_dataset_index()
        except Exception as ex:
            print("Error:  Check that you specified a label and index!")
            print(ex)

    # if we want to delete the dataset index
    elif (options.deleteDatasetIndex):
        es_delete_dataset_index()

    # we've exhausted all our options
    else:
        sys.exit(0)


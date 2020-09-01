import requests
import json
from datetime import datetime
import sys
import os


# Define some class constants

this = sys.modules[__name__]

# Read some defaults from OS environment if set

# Default DSpace REST API HOST name "DSPACE_HOSTNAME"
if 'DSPACE_HOSTNAME' in os.environ:
    this.hostname = os.environ['DSPACE_HOSTNAME']
else:
    this.hostname = 'dataspace.princeton.edu'

# Default OSTI DOE contract number value
if 'CONTRACT_NUMBER' in os.environ:
    this.contract_no = os.environ['CONTRACT_NUMBER']
else:
    this.contract_no = None

# default dataset content type for OSTI
this.dataset_type = 'SM'


# Define useful exception classes for error conditions.

class DataspaceException(Exception):
	""" Base error class for handlers. """
	def __init__(self, message="An error occurred."):
		self.message = message
		super().__init__(self.message)
	

class NotFoundException(DataspaceException):
	""" Record is not on file with REST API. """


class UnavailableException(DataspaceException):
	""" Record is unapproved or unavailable. """


# Metadata record
#

class Metadata(object):

    # Convert a STRING DATE VALUE to a DATETIME object
    # Attempt several date formats known to be valid before giving up.
    #
    @staticmethod
    def strtodate(value):
        for fmt in ('%Y-%m-%dT%H:%M:%SZ', '%Y-%m', '%Y-%m-%d', '%Y'):
            try:
                return datetime.strptime(value, fmt).strftime('%m/%d/%Y')
            except ValueError:
                pass
        raise ValueError('Invalid date format: ' + value)

    # Create a static metadata retrieval method
    # ITEM METADATA defined as a List of key-and-value pairs
    # Define the DSpace REST API host name as host
    # Indicate item ID via the ID
    #
    def __init__(self, id):
        self.id = id
        self.hostname = this.hostname
        self.contract_no = this.contract_no
        self.dataset_type = this.dataset_type

        # ask for JSON to retrieve metadata information
        headers = {"accept": "application/json"}
        request = requests.get("https://" + self.hostname + "/rest/items/" + str(id) + "/metadata",
                               verify=False,
                               headers=headers)

        if request.status_code == 200:
            self.data = json.loads(request.text)
        elif request.status_code == 404:
            raise NotFoundException('ID #' + str(id) + ' not found.')
        elif request.status_code == 401:
            raise UnavailableException("ID #" + str(id) + " is not available.")
        else:
            raise DSpaceException("ID #" + str(id) + " unknown error code #" + str(request.status_code))

    # Convert item Metadata to OSTI specific dictionary object
    #
    def toosti(self):
        """ Translate key-value metadata to OSTI tag dictionary. """
        record = {'accession_num': self.id,
                  'contract_nos': self.contract_no,
                  'dataset_type': self.dataset_type}

        creators = []
        identifiers = []

        for key in self.data:
            if key["key"] == "dc.title":
                record["title"] = key["value"]
            elif key["key"] == "dc.contributor.author" or key['key'] == 'dc.creator':
                creators.append(key["value"])
            elif key["key"] == "dc.identifier.uri":
                record["site_url"] = key["value"]
            elif key["key"] == "dc.publisher":
                record["research_org"] = key["value"]
            elif key["key"] == "dc.subject":
                record["keywords"] = key["value"]
            elif key["key"] == "dc.contributor.funder":
                record["sponsor_org"] = key["value"]
            elif key["key"] == "dc.description.abstract":
                record["description"] = key["value"]
            elif key["key"] == "dc.date.issued":
                record["publication_date"] = Metadata.strtodate(key["value"])
            elif key['key'] == 'dc.relation.ispartof':
                identifiers.append({'related_identifier': key['value'], 'relation_type': 'IsPartOf',
                                    'related_identifier_type': 'DOI'})
            elif key['key'] == 'dc.relation.isversionof':
                identifiers.append({'related_identifier': key['value'], 'relation_type': 'IsNewerVersionOf',
                                    'related_identifier_type': 'DOI'})
            elif key['key'] == 'dc.relation.hasversion':
                identifiers.append({'related_identifier': key['value'], 'relation_type': 'IsPreviousVersionOf',
                                    'related_identifier_type': 'DOI'})
            elif key['key'] == 'dc.relation.isreferencedby':
                identifiers.append({'related_identifier': key['value'], 'relation_type': 'IsReferencedBy',
                                    'related_identifier_type': 'DOI'})
            elif key['key'] == 'dc.relation.isbasedon':
                identifiers.append({'related_identifier': key['value'], 'relation_type': 'References',
                                    'related_identifier_type': 'DOI'})
            elif key['key'] == 'dc.relation.requires':
                identifiers.append({'related_identifier': key['value'], 'relation_type': 'Requires',
                                    'related_identifier_type': 'DOI'})

        # if related identifiers found, add them
        if identifiers:
            record['related_identifiers'] = identifiers

        # consolidate creators into a single string
        record["creators"] = "; ".join(creators)

        return record

# Define an object to iterate over Dataspace collection and retrieve
# individual record metadata for use in OSTI posting.
#

class CollectionItems(object):

    # Set up the Iterable for Collection Items for a given ID.
    # initial limit of 100 items per page, keep up with offset in REST calls.
    #
    def __init__(self, collectionid):
        """
        Create a CollectionItems iterator object based on indicated ID.

        :param collectionid: the collection ID to iterate
        """
        self.id = collectionid
        self.limit = 100
        self.offset = 0
        self.items = []
        self.hostname = this.hostname

    # Obtain more items from the Collection
    #
    def fetch(self):
        # ask for JSON for the next set of Items
        headers = {"accept": "application/json"}
        request = requests.get("https://" + self.hostname + "/rest/collections/" + str(self.id) + "/items?limit=" +
                               str(self.limit) + "&offset=" + str(self.offset),
                               verify=False,
                               headers=headers)

        # if we found items, set them and move the offset up
        if request.status_code == 200:
            self.items = json.loads(request.text)
            self.offset += self.items.__len__()
        else:
            print ("Warning: return code={}".format(request.status_code))
            self.items = []

    # Make this an Iterable class
    #
    def __iter__(self):
        return self

    # The next function: pop the first item on the list if any; if none, fetch more.  If done, stop iteration.
    #
    def __next__(self):
        if self.items:
            return self.items.pop(0)

        self.fetch()

        if self.items:
            return self.__next__()
        else:
            raise StopIteration


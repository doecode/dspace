DSpace-to-OSTI Dataset API Python module
========================================

Purpose
-------

Provide simple example python (3+) module for loading DSpace metadata 
available via public REST API to OSTI data set metadata service.

Requirements
------------

Assumes:
* python3 interpreter available (tested using version 3.6.8)
* ostiapi package installed (https://github.com/doecode/ostiapi)
* dependencies for above, including libraries: requests, dicttoxml

Usage
-----

Using the provided import.py script and OSTI login credentials, one may
import single records or collections from DSpace REST API records to OSTI.
Either an item ID or collection ID is required.  

Program usage may be viewed by invoking the example directly:

```$ python3 import.py

usage: import-dspace.py -d [dspace-host] -i [id] -c [id] -n [contractno] -u [username] -p [password] [--test]
 -h, --help: this usage information
 -d, --host: the DSpace API host name (default: dataspace.princeton.edu)
 -i, --id: single ID to import, or
 -c, --collection: collection ID to import
 -n, --contractno: default contract number for data (default: None)
 -u, --username: ELINK user account name
 -p, --password: ELINK account password
 -t, --test: post to OSTI test server; default is production

```

Note that if no username or password is supplied, the record(s), if found, 
will be printed out in OSTI XML format for debugging.  

The program will load defaults for certain configuration elements from 
the file **import.ini** if present in the same folder.  An example configuration
file may contain the following key names:

| Name | Usage/Description |
| --- | --- |
| hostname | The default DSpace API host name |
| contract_no | The default value for DOE contract number for OSTI |
| dataset_type | The dataset code to use as a default (e.g., 'SM') |
| username | The OSTI API user account name |
| password | The password for OSTI API login |

example **import.ini**
```
[DEFAULT]
hostname = dataspace.princeton.edu
username = my-elink-user
password = my-elink-password
contract_no = my-DOE-contract-number
```

Any configuration elements present in **import.ini** will be loaded and used
as defaults, and may be overridden by the command-line argument switches as
specified above.

Example usage:

```
$  python3 import.py -i 89667 -n 'my-contract-number' -d 'restapi.dspace.com'
```

The program presently outputs OSTI API response values (as JSON) if a valid
username and password credential set is passed in.  The records returned in
this manner may be iterated for various attributes containing OSTI unique
identifier ("osti_id"), record status ("status"), and record DOI ("doi").

The program return code indicates its disposition:

| Return Value | Description |
| --- | --- |
| 0 | No arguments given, usage printed |
| 1 | Invalid or incorrect arguments or switches provided |
| 400 | DSpace record ID is unavailable or not approved |
| 403 | Access is forbidden |
| 404 | DSpace record ID is not on file |
| 500 | OSTI posting error has occcured, or other system error |

Presently, the import script will simply print out the response objects
if posting to OSTI.  These are expressed in JSON dictionary objects, with
a key of 'record' and each element containing some key information, including:

| Element Name | Description |
| --- | --- |
| status | SUCCESS or FAILURE indiciating record state |
| status_message | Description of issue on FAILURE |
| osti_id | the unique OSTI identifier value |
| doi | the DOI registered for the record |
| title | the record title from DSpace |
| accession_num | the DSpace ID value |

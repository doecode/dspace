import getopt
import sys
import dataspace
from dataspace import Metadata
from dataspace import CollectionItems
from dataspace import(NotFoundException, UnavailableException)
import ostiapi
from ostiapi import ForbiddenException
import configparser

# print a usage message if no arguments passed
#
def usage():
    """
    Print a usage message for help.

    :return: None
    """
    print ("usage: import-dspace.py -d [dspace-host] -i [id] -c [id] -n [contractno] -u [username] -p [password] [--test]")
    print ("  (loads configuration from import.cfg if present)\n")
    print (" -h, --help: this usage information")
    print (" -d, --host: the DSpace API host name (default: {})".format(dataspace.hostname))
    print (" -i, --id: single ID to import, or")
    print (" -c, --collection: collection ID to import")
    print (" -n, --contractno: default contract number for data (default: {})".format(dataspace.contract_no))
    print (" -u, --username: ELINK user account name")
    print (" -p, --password: ELINK account password")
    print (" -t, --test: post to OSTI test server; default is production\n")


# Load a named key value from DEFAULT configuration parser if present
# If not, returns None.
#
def get_default_from(config, key):
    return config['DEFAULT'][key] if key in config['DEFAULT'] else None


# main program starts
config = configparser.ConfigParser()
config.read('import.ini')

argv = sys.argv[1:]
idnumber = None
collectionid = None
username = get_default_from(config, 'username')
password = get_default_from(config, 'password')
dataspace.contract_no = get_default_from(config, 'contract_no')
dataspace.hostname = get_default_from(config, 'hostname')
dataspace.dataset_type = get_default_from(config, 'dataset_type')

try:
    opts, args = getopt.getopt(argv, 'd:i:c:u:n:p:ht', ['host=', 'id=', 'collection=', 'username=', 'contractno=' 'password=', 'help', 'test'])

    for o, a in opts:
        if o in ('-i', '--id'):
            idnumber = a
        elif o in ('-c', '--collection'):
            collectionid = a
        elif o in ('-u', '--username'):
            username = a
        elif o in ('-p', '--password'):
            password = a
        elif o in ('-d', '--host'):
            dataspace.hostname = a
        elif o in ('-n', '--contractno'):
            dataspace.contract_no = a
        elif o in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif o in ('-t', '--test'):
            ostiapi.testmode()
        else:
            assert False, "Unhandled argument."

except getopt.GetoptError as error:
    print (error)
    usage()
    sys.exit()

if idnumber == None and collectionid == None:
    print ("Item or Collection ID is required.")
    usage()
    sys.exit()

records = []
if idnumber:
    try:
        records.append(Metadata(idnumber).toosti())
    except NotFoundException:
        print ("ID number was not found.")
        sys.exit(404)
    except UnavailableException:
        print ("ID number is not accessible.")
        sys.exit(400)
else:
    for item in CollectionItems(collectionid):
        try:
            records.append(Metadata(item["id"]).toosti())
        except NotFoundException:
            print ("Warning: ID " + item["id"] + " not found, skipping.")
        except UnavailableException:
            print ("Warning: ID " + item['id'] + " is not available, skipping.")

# Post to OSTI and return response if username is present
# Otherwise, simply print out the XML that would have submitted
if username:
      try:
          response = ostiapi.post(records, username, password)
      except ForbiddenException:
          print ('Access to post records to ELINK is forbidden.')
          sys.exit(403)
      except ServerException as e:
          print ('Unknown error occurred posting record #{}: {}'.format(count, e.message))
          sys.exit(500)

      print (response)
else:
      print (ostiapi.datatoxml(records))

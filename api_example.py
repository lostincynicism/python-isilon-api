#API Usage Example
#==========
#To use: Modify the fqdn, username, and password
# Create a directory called /ifs/data/test on your cluster
import isilon
import time

fqdn = 'kcisilon.kcdemo.local'  #change to your cluster
username = 'root'
password = 'a'

#connect
api = isilon.API(fqdn, username, password)

#Check for old bad snaps and delete
try:
    api.platform.snap('testsnap')          #Get info for testsnap, with throw exception if not found
    print("We found an existing testsnap,let's delete that...")
    api.platform.snap_delete('testsnap')  
except isilon.ObjectNotFound:
    pass


#More Error handling examples
try:
    api.platform.snap_create('testsnap','/ifs/data/test')
except isilon.APIError, e:
    print("Snapshot Creation error: %s",e)

#list all snaps
print('\nListing of All Snaps:')
for snap in api.platform.snap():
    print("Name: %s, Path: %s, Created: %s" % (snap['name'], snap['path'], time.ctime(snap['created']) ))

#cleanup our testnsap
api.platform.snap_delete('testsnap')

#namespace example
print("\nIs /ifs/data/test a dir? %s" %( api.namespace.is_dir('/ifs/data/test')))
print("\nListing for /ifs/data/test")
for item in api.namespace.dir('/ifs/data/test'):
    print("Item Name: %s , type: %s" % (item['name'], item['type'] ) )
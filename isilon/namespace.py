import json
import logging
import time
from pprint import pprint

from .exceptions import ( ObjectNotFound, IsilonLibraryError )



class Namespace(object):

    '''Implements higher level functionality to interface with an Isilon cluster'''

    def __init__(self, session):
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.NullHandler())
        self.session = session
        self.namespace_url = '/namespace'
                  
        #initialize session timeout values
        self.timeout = 0

    def _override(self,params,overrides):
        '''copy overrides into params dict, so user can specify additional params not specifically layed out'''
        for (k,v) in overrides.items():
            params[k] = v
        return params
    
    def api_call(self,method, url,**kwargs):
        '''add the namespace prefix to the api call'''
        return self.session.api_call(method, self.namespace_url + url,**kwargs)
        
    def api_call_resumeable(self,method,url,**kwargs):
        '''add the namespace prefix to the api call'''
        return self.session.api_call_resumeable(method,self.namespace_url + url,**kwargs)
           
    def accesspoint(self):
        r = self.api_call("GET", "")
        
        data = r['namespaces']
        
        #move all the name, value pairs into an actual dictionary for easy use.
        
        results = {}
        for x in data:
            results[ x['name'] ] = x['path']
        return results

        
    
    def accesspoint_create(self,name,path):
        data = { 'path': path }
        r = self.api_call("PUT",  '/' + name.strip('/'), data=json.dumps(data) )
    
    def accesspoint_delete(self,name):
        r = self.api_call("DELETE",  '/' + name.strip('/') )
 
    def accesspoint_setacl(self,name,acl):
        self.acl_set('/' + name,acl,nsaccess=True)
 
    def accesspoint_getacl(self,name):
        return self.acl('/' + name,nsaccess=True)
    
    
    def acl(self,path,nsaccess=False):
        '''get acl'''       
        options = "?acl"
        if nsaccess:
            options += "&nsaccess=true"
        try:
            return self.api_call("GET", path + options)
        except ObjectNotFound:
            return None

    def acl_set(self,path,acls,nsaccess=False):
        '''set acl'''
        options = "?acl"
        if nsaccess:
            options += "&nsaccess=true"
        acls['authoritative'] = "acl"
        r = self.api_call("PUT", path + options,data=json.dumps(acls))
   
    
    def metadata(self,path):
        '''get metadata'''        
        options = "?metadata"
        try:
            data = self.api_call("GET", path + options)
        except ObjectNotFound:
            return None
        
        if not 'attrs' in data:
            return None
        data = data['attrs']
        
        #move all the name, value pairs into an actual dictionary for easy use.
        results = {}
        for x in data:
            #print(x)
            results[ x['name'] ] = x['value']
        return results
        
    def metatdata_set(self,path,metadata):
        pass
        
                    
    def file_copy(self,src_path, dst_path, clone=False, snapshot=None):
        '''Copy a file''' 
        options={'clone' : clone}
        if clone and snapshot:
            options['snapshot'] =  snapshot
        headers = { "x-isi-ifs-copy-source" :  "/namespace" + src_path }    
        return self.api_call("PUT", dst_path, params=options, headers=headers)
        
    def file_create(self, path, data, overwrite=False ):
        '''Uploads a file '''
        headers = { "x-isi-ifs-target-type" : "object" , 'content-type' : 'application/octet-stream' }  
        return self.api_call("PUT", path , data=data, params={'overwrite' : overwrite}, headers=headers)
    
    def file(self,path,**kwargs):
        try:
            return self.api_call("GET", path,params=kwargs)
        except ObjectNotFound:
            return None
        
    def file_delete(self,path):
        return self.api_call("DELETE", path)
    
    

    def dir(self,path,**kwargs):
        '''Get directory listing'''
        params = self._override({'detail':'type'},kwargs)        
        #Resumable catches object not found a returns an empty list
        return self.api_call_resumeable("GET", path,params=params)
          
    def exists(self,path):
        if self.metadata(path):
            return True
        return False
    
    def is_dir(self,path):
        metadata = self.metadata(path)
        
        if metadata and 'type' in metadata and metadata['type'] == "container" :
            return True
        return False

        
    def dir_create(self,path,recursive=True):
        '''Create a new directory'''  
        headers = { "x-isi-ifs-target-type" : "container" }   
        options={'recursive' : recursive }
        r = self.api_call("PUT", path, params=options, headers=headers)
    
    
    def dir_delete(self,path):
        '''delete a directory'''  
        options=""
        r = self.api_call("DELETE", path + options)

 
        
        

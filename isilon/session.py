import json
import requests
import httplib
import logging
import time
from pprint import pprint
import sys
import socket

from .exceptions import ( ConnectionError, ObjectNotFound, APIError )

class Session(object):

    '''Implements higher level functionality to interface with an Isilon cluster'''

    def __init__(self, fqdn, username, password, services):
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.NullHandler())
        self.ip = socket.gethostbyname(fqdn)
        self.url= "https://" + self.ip + ':8080'
        self.session_url = self.url + '/session/1/session'

        self.username = username
        self.password = password
        self.services = services
        
        #Create HTTPS Requests session object
        self.s = requests.Session()
        self.s.headers.update({'content-type': 'application/json'})
        self.s.verify = False
        
        #initialize session timeout values
        self.timeout = 0
        self.r = None
        
    
    def log_api_call(self,r,lvl):
        
        self.log.log(lvl, "===========+++ API Call=================================================================")
        self.log.log(lvl,"%s  %s , HTTP Code: %d" % (r.request.method, r.request.url, r.status_code))
        self.log.log(lvl,"Request Headers: %s" % r.request.headers)
        self.log.log(lvl,"Request Data : %s" % (r.request.body))
        self.log.log(lvl,"")
        self.log.log(lvl,"Response Headers: %s " % r.headers )
        self.log.log(lvl,"Response Data: %s" % (r.text.strip()))
        self.log.log(lvl,"=========================================================================================")

    def debug_last(self):
        if self.r:
            self.log_api_call(self.r,logging.ERROR)

    def api_call(self,method,url,**kwargs):
    	
        #check to see if there is a valid session 
        if time.time() > self.timeout:
            self.connect()        

        url = self.url + url
        print url
        if len(url) > 8198:      
            self.log.exception("URL Length too long: %s", url)
        
        r = self.s.request(method,url,**kwargs)
                 
        #check for authorization issue and retry if we just need to create a new session
        if r.status_code == 401:
            #self.bad_call(r)
            logging.info("Authentication Failure, trying to reconnect session")
            self.connect()
            r = self.s.request(method,url,**kwargs)
        
        
        if r.status_code == 404:      
            raise ObjectNotFound()
        elif r.status_code == 401:
            self.log_api_call(r,logging.ERROR)
            raise APIError("Authentication failure")
        elif r.status_code > 204:
            self.log_api_call(r,logging.ERROR)
            message = "API Error: %s" % r.text
            raise APIError(message)
        
        self.log_api_call(r,logging.DEBUG)
        self.r = r
        return r
            
            
            
    def api_call_resumeable(self,object_name,method,url,**kwargs):
        #initialize state for resuming    
        last_page = False
        resume=None
        
        #We will loop through as many api calls as needed to retrieve all items
        while not last_page:
            
            #if we have a resume token we need to add it to our params
            if resume != None:
                #If the params key doesn't exist we need to create it.
                if not 'params' in kwargs:
                    kwargs['params'] = {}
                
                #Set the resume token    
                kwargs['params']['resume'] = resume
            
            #Make API Call
            r = self.api_call(method, url, **kwargs)
            data = r.json()
        
            #Check for a resume token for mutliple pages of results
            if 'resume' in data:
                resume = data['resume']
                last_page = False
            else:
            	last_page = True

            if object_name in data:    
                for obj in data[object_name]:
                    yield obj
            
        return
      

    def connect(self):
        
        #Get an API session cookie from Isilon
        #Cookie is automatically added to HTTP requests session
        logging.debug("--> creating session")
        sessionjson = json.dumps({'username': self.username , 'password': self.password , 'services': self.services})
        
        r = self.s.post(self.session_url,data=sessionjson) 
        if r.status_code != 201 :
            #r.raise_for_status()
            self.log_api_call(r,logging.ERROR)
            raise ConnectionError(r.text)
            
        #Renew Session 60 seconds prior to our timeout
        self.timeout = time.time() + r.json()['timeout_absolute'] - 60
        logging.debug("New Session created! Current clock %d, timeout %d" % (time.time(),self.timeout))
        return True

         
#!/usr/bin/env python

__package__    = "wsclustr"
__author__     = "Aaron Straup Cope"
__url__        = "http://www.aaronland.info/python/wsclustr"
__copyright__  = "Copyright (c) 200 Aaron Straup Cope. BSD license : http://www.modestmaps.com/license.txt"

# shared imports

import urllib2
import time
import os.path
import hashlib
import time

class wsclustr :

    def __init__ (self, **kwargs) :
    
        self.wsclustr_hostname = None
        self.wsclustr_endpoint = 'ws-clustr/'
        self.verbose = False

        if kwargs.has_key('hostname') :
            self.wsclustr_hostname = kwargs['hostname']

        if kwargs.has_key('endpoint') :
            self.wsclustr_endpoint = kwargs['endpoint']

        if kwargs.has_key('verbose') :
            self.verbose = kwargs['verbose']
        
    #
    # Stuff you may want to override
    #
    
    def startup (self, **kwargs) :
        return True
    
    def ready (self) :
        return True

    def shutdown (self) :
        return True

    def hostname (self) :
        return self.wsclustr_hostname

    def endpoint (self) :
        return self.wsclustr_endpoint
    
    #
    # Stuff you probably don't need to touch
    #
    
    def clustr (self, points, **kwargs) :

        if self.verbose :
            print "clustr: %s" % points
        
        url = "http://%s/%s" % (self.hostname(), self.endpoint())

        req = urllib2.Request(url)
        
        if kwargs.has_key('alpha') and kwargs['alpha'] :

            if self.verbose :
                print "alpha: %s" % kwargs['alpha']
                
            req.add_header('x-clustr-alpha', kwargs['alpha'])

        if kwargs.has_key('filename') and kwargs['filename'] :
            shortname = os.path.basename(kwargs['filename'])
            shortname = shortname.replace(".tar.gz", "")            

            if self.verbose :
                print "filename: %s" % shortname
     
            req.add_header('x-clustr-name', shortname)

        #
        # what to send?
        #
        
        if kwargs.has_key('try_cache') and kwargs['try_cache'] :
            md5 = self._md5sum(points)
            req.add_header('x-clustr-cache', 'clustr-%s' % md5)

            if self.verbose :
                print "try cached version with key: %s" % md5
                
        else :

            try:
                fh = open(points, 'rb')
            except Exception, e :
                print "failed to open '%s' for reading, %s" % (points, e)
                return False

            body = fh.read()

            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            req.add_header('Content-Length', len(body))
            req.add_data(body)

        #
        # Go!
        #
        
        if self.verbose :
            print "connect to %s" % url
            
        try :
            response = urllib2.urlopen(req)

        except urllib2.HTTPError, e :

            if e.code == 404 and kwargs.has_key('try_cache') and kwargs['try_cache']:

                if self.verbose :
                    print "try again without cache"
                
                kwargs['try_cache'] = 0
                return self.clustr(points, **kwargs)

            print "failed to clustr '%s' using '%s', %s" % (points, url, e)
            return False
        
        except Exception, e :
            print "failed to clustr '%s' using '%s', %s" % (points, url, e)
            return False

        headers = response.headers

        if self.verbose :
            print "return headers: '%s'" % str(headers)
            
        try :
            fname = headers['x-clustr-filename']
            
        except Exception, e:

            if kwargs.has_key('filename') and kwargs['filename'] :
            	shortname = os.path.basename(kwargs['filename'])
            	fname = shortname.replace(".tar.gz", "")            
            else :
            	fname = os.path.basename(points)

	#
        
        if kwargs.has_key('filename') and kwargs['filename'] :
            fname = os.path.join(os.path.dirname(kwargs['filename']), fname)

        #
        
        try :
            fh = open(fname, 'wb')
        except Exception, e:
            print "failed to open '%s' for writing, %s" % (fname, e)
            return False
        
        fh.write(response.read())
        fh.close()

        if self.verbose :
            print "return: %s" % fname
            
        return fname

    def _md5sum (self, path) :

        m = hashlib.md5()
        
        fh = open(path,"rb")

        for ln in fh.readlines() :
            m.update(ln)

        return m.hexdigest()

#
# ws-clustr on EC2
#

class ec2 (wsclustr) :

    def __init__ (self, **kwargs) :

        wsclustr.__init__(self, **kwargs)

        self.is_ready = False
        self.instance = None        
        self.reservation = None

        try :
            from boto.ec2.connection import EC2Connection
            self.conn = EC2Connection(kwargs['access_key'], kwargs['secret_key'])
            self.is_ready = True
        
        except Exception, e :
            print "failed to create EC2 connection: %s" % e

    def hostname (self) :
        return self.instance.public_dns_name
    
    def startup (self, **kwargs) :
        
        if self.verbose :
            print "startup: %s" % kwargs['ami']
            
        if self.instance :
            return

        if self.reservation :
            return

        for r in self.conn.get_all_instances() :
            for i in r.instances :
                
                if i.image_id == kwargs['ami'] and i.state == 'running' :
                    self.is_ready = True
                    self.instance = i
                    return
    
        self.reservation = self.conn.run_instances(kwargs['ami'])
    
    def ready (self) :

        if self.is_ready :

            if self.verbose :
                print "status: running"
            
            return True
        
        i = self.reservation.instances[0]

        if self.verbose :
            print "status: %s" % i.update()
            
        if i.update() == 'running' :
            
            self.is_ready = True
            self.instance = i
            
            return True

        return False
    
    def shutdown (self) :

        if self.verbose :
            print "shutdown"
            
        i = self.instance
        i.stop()

#
# Hello world
#

if __name__ == '__main__' :

    import optparse
    
    parser = optparse.OptionParser()
    parser.add_option("-P", "--points", dest="points", help="the path of the points file to clustrize")
    parser.add_option("-C", "--try_cache", dest="try_cache", help="first ask ws-clustr to use a cached version of your points file", default=False, action='store_true')    
    parser.add_option("-a", "--alpha", dest="alpha", help="the size of the alpha to clustr the points file with", default=None)
    parser.add_option("-f", "--filename", dest="filename", help="the name of your shapefile", default=None)        
    parser.add_option("-t", "--terminate", dest="terminate", help="terminate the AMI instance", default=False, action='store_true')
    parser.add_option("-v", "--verbose", dest="verbose", help="enable verbose logging", default=False, action='store_true')
    
    (opts, args) = parser.parse_args()

    points = opts.points
    alpha = opts.alpha
    fname = opts.filename
    try_cache = opts.try_cache

    clustr = wsclustr(hostname='http://localhost', verbose=verbose)

    clustr.startup()
    
    while not clustr.ready() :
        time.sleep(5)

    shpfile = clustr.clustr(points, alpha=alpha, filename=fname, try_cache=try_cache)
    
    if opts.terminate :
        clustr.shutdown()

    print "shapefile created and stored in %s" % shpfile

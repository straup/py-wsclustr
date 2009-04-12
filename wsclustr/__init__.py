#!/usr/bin/env python

__package__    = "wsclustr"
__author__     = "Aaron Straup Cope"
__url__        = "http://www.aaronland.info/python/wsclustr"
__copyright__  = "Copyright (c) 200 Aaron Straup Cope. BSD license : http://www.modestmaps.com/license.txt"

from boto.ec2.connection import EC2Connection
import urllib2
import time
import os.path
import hashlib

class wsclustr :

    def __init__ (self, access_key, access_secret, verbose=False) :
    
        self.conn = EC2Connection(access_key, secret_key)

        self.is_ready = False
        self.instance = None        
        self.reservation = None

        # Note the trailing slash to prevent
        # 301 redirects and making the baby
        # python cry...
        
        self.endpoint = 'ws-clustr/'

        self.verbose = verbose
        
    #
    
    def startup (self, ami) :

        if self.verbose :
            print "startup: %s" % ami
            
        if self.instance :
            return

        if self.reservation :
            return

        for r in self.conn.get_all_instances() :
            for i in r.instances :
                if i.image_id == ami :
                    self.is_ready = True
                    self.instance = i
                    return
    
        self.reservation = self.conn.run_instances(ami)

    #
    
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

    #

    def clustr (self, points, **kwargs) :

        if self.verbose :
            print "clustr: %s" % points
            
        #
        
        host = self.instance.public_dns_name
        url = "http://%s/%s" % (host, self.endpoint)

        req = urllib2.Request(url)
        
        #
                    
        if kwargs.has_key('alpha') and kwargs['alpha'] :

            if self.verbose :
                print "alpha: %s" % kwargs['alpha']
                
            req.add_header('x-clustr-alpha', kwargs['alpha'])

        if kwargs.has_key('filename') and kwargs['filename'] :
            shortname = os.path.basename(kwargs['filename'])
            shortname = shortname.replace(".tar.gz", "")            

            if self.verbose :
                print "filename: %s" % kwargs['filename']
                
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

            if e.code == 404 and kwargs.has_key('try_cache') :

                if self.verbose :
                    print "try again without cache"
                
                kwargs['try_cache'] = 0
                return self.clustr(points, **kwargs)

            print "failed to clustr '%s' using '%s', %s" % (points, url, e)
            return False
        
        except Exception, e :
            print "failed to clustr '%s' using '%s', %s" % (points, url, e)
            return False

        #

        headers = response.headers
        fname = headers['x-clustr-filename']

        if kwargs.has_key('filename') and kwargs['filename'] :
            fname = kwargs['filename']

        #
        
        try :
            fh = open(fname, 'wb')
        except Exception, e:
            print "failed to open '%s' for writing, %s" % (fname, e)
            return False
        
        fh.write(response.read())
        fh.close()

        #

        if self.verbose :
            print "return: %s" % fname
            
        return fname
    
    #
    
    def shutdown (self) :

        if self.verbose :
            print "shutdown"
            
        i = self.instance
        i.stop()

    #

    def _md5sum (self, path) :

        m = hashlib.md5()
        
        fh = open(path,"rb")

        for ln in fh.readlines() :
            m.update(ln)

        return m.hexdigest()

                                                                                    
if __name__ == '__main__' :

    import optparse
    import ConfigParser
    
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config", dest="config", help="path to an ini config file")
    parser.add_option("-A", "--ami", dest="ami", help="the name of the EC2 AMI to use")
    parser.add_option("-P", "--points", dest="points", help="the path of the points file to clustrize")
    parser.add_option("-C", "--try_cache", dest="try_cache", help="first ask ws-clustr to use a cached version of your points file", default=False, action='store_true')    
    parser.add_option("-a", "--alpha", dest="alpha", help="the size of the alpha to clustr the points file with", default=None)
    parser.add_option("-f", "--filename", dest="filename", help="the name of your shapefile", default=None)        
    parser.add_option("-t", "--terminate", dest="terminate", help="terminate the AMI instance", default=False, action='store_true')
    parser.add_option("-v", "--verbose", dest="verbose", help="enable verbose logging", default=False, action='store_true')
    
    (opts, args) = parser.parse_args()

    cfg = ConfigParser.ConfigParser()
    cfg.read(opts.config)

    access_key = cfg.get("aws", "access_key")
    secret_key = cfg.get("aws", "secret_key")

    ami = opts.ami
    points = opts.points
    alpha = opts.alpha
    fname = opts.filename
    try_cache = opts.try_cache

    clustr = wsclustr(access_key, secret_key, opts.verbose)

    clustr.startup(ami)
    
    while not clustr.ready() :
        time.sleep(5)

    shpfile = clustr.clustr(points, alpha=alpha, filename=fname, try_cache=try_cache)
    
    if opts.terminate :
        clustr.shutdown()

    print "shapefile created and stored in %s" % shpfile

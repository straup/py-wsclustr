#!/usr/bin/env python

from boto.ec2.connection import EC2Connection
import urllib2
import time
import os.path

class wsclustr :

    def __init__ (self, access_key, access_secret, verbose=False) :
    
        self.conn = EC2Connection(access_key, secret_key)

        self.is_ready = False
        self.ami = None
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
            
        try:
            fh = open(points, 'rb')
        except Exception, e :
            print "failed to open '%s' for reading, %s" % (points, e)
            return False

        body = fh.read()
        
        #
        
        host = self.instance.public_dns_name
        url = "http://%s/%s" % (host, self.endpoint)

        req = urllib2.Request(url)

        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        req.add_header('Content-Length', len(body))
            
        if kwargs.has_key(alpha) and kwargs['alpha'] :

            if self.verbose :
                print "alpha: %s" % kwargs['alpha']
                
            req.add_header('x-clustr-alpha', kwargs['alpha'])

        if kwargs.has_key('filename') and kwargs['filename'] :
            shortname = os.path.basename(kwargs['filename'])
            shortname = shortname.replace(".tar.gz", "")            

            req.add_header('x-clustr-name', shortname)

        req.add_data(body)

        if self.verbose :
            print "connect to %s" % url
        
        try :            
            response = urllib2.urlopen(req)
        except Exception, e :
            print "failed to clustr '%s' using '%s', %s" % (points, url, e)
            return False

        if response.code != 200 :
            print "failed to clustr '%s' with http error: %s, %s" % (points, response.code, response.msg)
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
            print "return %s" % fname
            
        return fname
    
    #
    
    def shutdown (self) :

        if self.verbose :
            print "shutdown"
            
        i = self.instance
        i.stop()

    #
    
if __name__ == '__main__' :

    import optparse
    import ConfigParser
    
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config", dest="config", help="path to an ini config file")
    parser.add_option("-A", "--ami", dest="ami", help="the name of the EC2 AMI to use")
    parser.add_option("-P", "--points", dest="points", help="the path of the points file to clustrize")
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
    
    clustr = wsclustr(access_key, secret_key, opts.verbose)

    clustr.startup(ami)
    
    while not clustr.ready() :
        time.sleep(5)

    clustr.clustr(points, alpha=alpha, filename=fname)
    
    if opts.terminate :
        clustr.shutdown()

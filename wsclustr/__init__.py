#!/usr/bin/env python

from boto.ec2.connection import EC2Connection
import time
import urllib2

class wsclustr :

    def __init__ (self, access_key, access_secret) :
    
        self.conn = EC2Connection(access_key, secret_key)

        self.is_ready = False
        self.instance = None        
        self.reservation = None

        self.endpoint = 'ws-clustr'
        
    #
    
    def startup (self, ami) :

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
            return True
        
        i = self.reservation.instances[0]

        if i.update() == 'running' :
            
            self.is_ready = True
            self.instance = i
            
            return True

        return False

    #

    def clustr (self, points, alpha=None, fname=None) :

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
            
        if alpha :
            req.add_header('x-clustr-alpha', alpha)

        if fname :
            req.add_header('x-clustr-name', fname)

        req.add_data(body)

        # timing out...WTF?
        
        try :            
            response = urllib2.urlopen(req)
        except Exception, e :
            print "failed to clustr '%s' using '%s', %s" % (points, url, e)
            return False
        
        print response.read()
        
    #
    
    def shutdown (self) :

        i = self.instance
        i.stop()

    #
    
if __name__ == '__main__' :

    import optparse
    import ConfigParser
    
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config", dest="config", help="path to an ini config file")
    parser.add_option("-A", "--ami", dest="ami", help="the name of the EC2 AMI to use")
    parser.add_option("-p", "--points", dest="points", help="the path of the points file to clustrize")
    parser.add_option("-a", "--alpha", dest="alpha", help="the size of the alpha to clustr the points file with", default=None)
    parser.add_option("-n", "--name", dest="name", help="the name of your shapefile", default=None)        

    (opts, args) = parser.parse_args()

    cfg = ConfigParser.ConfigParser()
    cfg.read(opts.config)

    access_key = cfg.get("aws", "access_key")
    secret_key = cfg.get("aws", "secret_key")

    ami = opts.ami
    points = opts.points
    alpha = opts.alpha
    name = opts.name
    
    #
    
    clustr = wsclustr(access_key, secret_key)
    clustr.startup(ami)
    
    while not clustr.ready() :
        print "not ready..."
        time.sleep(5)

    clustr.clustr(points, alpha, name)

    """
    clustr.shutdown()
    """

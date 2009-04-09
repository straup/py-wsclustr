#!/usr/bin/env python

from boto.ec2.connection import EC2Connection
import time

class wsclustr :

    def __init__ (self, access_key, access_secret) :
    
        self.conn = EC2Connection(access_key, secret_key)

        self.is_ready = False
        self.instance = None        
        self.reservation = None

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

    def clustr (self) :

        host = self.instance.public_dns_name
        path = 'ws-clustr'

        print "http://%s/%s" % (host, path)
        
    #
    
    def shutdown (self) :

        i = self.instance
        i.stop()

        
if __name__ == '__main__' :

    import optparse
    import ConfigParser
    
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config", dest="config", help="path to an ini config file")
    parser.add_option("-a", "--ami", dest="ami", help="the name of the EC2 AMI to use")    

    (opts, args) = parser.parse_args()

    cfg = ConfigParser.ConfigParser()
    cfg.read(opts.config)

    access_key = cfg.get("aws", "access_key")
    secret_key = cfg.get("aws", "secret_key")
    ami = opts.ami
    
    #
    
    clustr = wsclustr(access_key, secret_key)
    clustr.startup(ami)
    
    while not clustr.ready() :
        print "not ready..."
        time.sleep(5)

    clustr.clustr()

    """
    clustr.shutdown()
    """

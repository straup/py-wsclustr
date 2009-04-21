#!/usr/bin/env python

if __name__ == '__main__' :
    
    import sys
    import os.path

    #
    # Where is wsclustr?
    #
    
    path_example = os.path.abspath(sys.argv[0])
    path_grandparent = os.path.dirname(os.path.dirname(path_example))
    sys.path.insert(0, path_grandparent)

    import wsclustr

    #
    # Go!
    #
    
    import optparse
    
    parser = optparse.OptionParser()
    parser.add_option("-P", "--points", dest="points", help="the path of the points file to clustrize")
    parser.add_option("-H", "--host", dest="hostname", help="the hostname that ws-clustr is running on", default="localhost")
    parser.add_option("-E", "--endpoint", dest="endpoint", help="the endpoint that ws-clustr is running on", default="ws-clustr/")
    parser.add_option("-C", "--try_cache", dest="try_cache", help="first ask ws-clustr to use a cached version of your points file", default=False, action='store_true')    
    parser.add_option("-a", "--alpha", dest="alpha", help="the size of the alpha to clustr the points file with", default=None)
    parser.add_option("-f", "--filename", dest="filename", help="the name of your shapefile", default=None)        
    parser.add_option("-t", "--terminate", dest="terminate", help="terminate the AMI instance", default=False, action='store_true')
    parser.add_option("-v", "--verbose", dest="verbose", help="enable verbose logging", default=False, action='store_true')
    
    (opts, args) = parser.parse_args()

    clustr = wsclustr.wsclustr(hostname=opts.hostname, endpoint=opts.endpoint)    
    shpfile = clustr.clustr(opts.points, alpha=opts.alpha, filename=opts.filename, try_cache=opts.try_cache)

    if opts.terminate :
        clustr.shutdown()

    print "shapefile created and stored in %s" % shpfile

#!/usr/bin/env python

if __name__ == '__main__' :
    
    import sys
    import os.path
    import tarfile
    
    #
    # Where is wsclustr?
    #
    
    path_example = os.path.abspath(sys.argv[0])
    path_grandparent = os.path.dirname(os.path.dirname(path_example))
    sys.path.insert(0, path_grandparent)

    import wsclustr

    #
    # Can has cheezburger?
    #
    
    try :
        import shpUtils
    except Exception, e :
        print "You will need to install the shpUtils package for this example to work."
        print "http://indiemaps.com/blog/2008/03/easy-shapefile-loading-in-python/"
        print "Error was: %s" % e
        sys.exit()

    try :
        from shapely.geometry import Polygon
    except Exception, e:
        print "You will need to install the Shapely package for this example to work."
        print "http://pypi.python.org/pypi/Shapely/"
        print "Error was: %s" % e
        sys.exit()

    #
    # Go!
    #
    
    import optparse
    import ConfigParser
    import time
    
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config", dest="config", help="path to an ini config file")
    parser.add_option("-E", "--endpoint", dest="endpoint", help="the endpoint that ws-clustr is running on", default="ws-clustr/")
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

    clustr = wsclustr.ec2(access_key=access_key, secret_key=secret_key, endpoint=opts.endpoint, verbose=opts.verbose)

    clustr.startup(ami=opts.ami)
    
    while not clustr.ready() :
        time.sleep(5)

    shpfile = clustr.clustr(opts.points, alpha=opts.alpha, filename=opts.filename, try_cache=opts.try_cache)
    
    if opts.terminate :
        clustr.shutdown()

    print "shapefile created and stored in %s" % shpfile

    #
    
    t = tarfile.open(shpfile)    
    t.extractall()

    shp = shpfile.replace(".tar.gz", "")
    shp = "%s/%s.shp" % (shp, shp)

    #
    
    polys = []

    print shp
    
    for record in shpUtils.loadShapefile(shp) :

        print record
        continue
    
        for part in record['shp_data']['parts'] :

            poly = []
            
            for pt in part['points'] :
                if pt.has_key('x') and pt.has_key('y') :
                    poly.append((pt['x'], pt['y']))

            poly = tuple(poly)
            p = Polygon(poly)

            polys.append(p)
            
    print "%s shapely.py polygons" % len(polys) 

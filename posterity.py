#!/usr/bin/env python

import sys
import getopt
import urllib
import xml.dom.minidom

def usage():
    print "Usage"

def parse_node(item):
    """Take a node object representing a single <item> in the Instapaper RSS 
    feed and return its information as a dictionary.
    """
    dict = {}
    for field in ('title', 'link', 'description', 'pubDate'):
        if item.getElementsByTagName(field)[0].hasChildNodes():
            dict[field] = item.getElementsByTagName(field)[0].firstChild.data
    return dict

def fetch_via_rss(url):
    """Take the url to the instapaper Archive RSS feed (this will change in the 
    future) and return a list containing Node objects.  Each object in the list
    represents a single <item> in the RSS feed.
    """
    # Retrieve the Archive RSS feed
    try:
        xml_object = urllib.urlopen(url)
    except:
        print "There was an error retrieving the RSS feed"

    # Create a Document
    dom = xml.dom.minidom.parse(xml_object)

    # Return the list
    return dom.getElementsByTagName('item')


def main():
    instapaper_archive_rss = "YOUR INSTAPAPER ARCHIVE FEED"

    # Parse arguments with getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hr", ["help", "rss"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    # If no options have been given --rss is the default
    if not opts:
        opts = [("--rss", "")]

    # What to do with given options
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-r", "--rss"):
            for item in fetch_via_rss(instapaper_archive_rss):
                print repr(parse_node(item))

if __name__ == "__main__":
    main()

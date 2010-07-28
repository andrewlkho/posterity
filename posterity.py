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

def retrieve_rss(url):
    """Temporary stub function to retrieve RSS feed and print information."""
    # Retrive the Archive RSS feed
    try:
        xml_object = urllib.urlopen(url)
    except:
        print "There was an error retrieving the RSS feed"

    # Create a Document
    dom = xml.dom.minidom.parse(xml_object)

    for item in dom.getElementsByTagName('item'):
        print repr(parse_node(item))

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
            retrieve_rss(instapaper_archive_rss)

if __name__ == "__main__":
    main()

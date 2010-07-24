#!/usr/bin/env python

import urllib
import xml.dom.minidom

def parseItem(item):
    """Take a node object representing a single <item> in the Instapaper RSS 
    feed and return its information as a dictionary.
    """
    dict = {}
    for field in ('title', 'link', 'description', 'pubDate'):
        if item.getElementsByTagName(field)[0].hasChildNodes():
            dict[field] = item.getElementsByTagName(field)[0].firstChild.data
    return dict


# Retrive the Archive RSS feed
try:
    xml_object = urllib.urlopen('YOUR INSTAPAPER ARCHIVE FEED')
except:
    print "There was an error retrieving the RSS feed"

# Create a Document
dom = xml.dom.minidom.parse(xml_object)

for item in dom.getElementsByTagName('item'):
    print repr(parseItem(item))

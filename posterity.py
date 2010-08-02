#!/usr/bin/env python

import sys
import getopt
import re
import urllib
import urllib2
import cookielib
import xml.dom.minidom

instapaper_username = ""
instapaper_password = ""

def usage():
    pass

def login(username, password):
    """Login to instapaper.  If successful, returns True."""
    data = urllib.urlencode({"username" : username, "password" : password})
    request = urllib2.Request('http://www.instapaper.com/user/login', data)

    try:
        response = urllib2.urlopen(request)
    except:
        return False

    # Bit of a hack: instapaper only sets a cookie if login was successful
    if response.info().getheader("Set-Cookie"):
        return True
    else:
        return False

def parse_node(item):
    """Take a node object representing a single <item> in the Instapaper RSS 
    feed and return its information as a dictionary.
    """
    dict = {}
    for field in ('title', 'link', 'description', 'pubDate'):
        if item.getElementsByTagName(field)[0].hasChildNodes():
            dict[field] = item.getElementsByTagName(field)[0].firstChild.data
    return dict

def fetch_via_rss():
    """Fetch the instapaper Archive RSS feed and return a list containing Node
    objects.  Each object in the list represents a single <item> in the RSS
    feed.
    """
    # Find out the URL to the RSS feed and store it in rss_url
    try:
        archive_page = urllib2.urlopen("http://www.instapaper.com/archive")
    except:
        return False
    rss_regex = r'"(http://www\.instapaper\.com/archive/rss/[^"]*)"'
    rss_url = re.search(rss_regex, archive_page.read()).group(1)

    # Return a list of Node objects, each representing an <item>
    try:
        rss = urllib2.urlopen(rss_url)
    except:
        return False
    rss_dom = xml.dom.minidom.parse(rss)
    return rss_dom.getElementsByTagName('item')

def main():
    # Parse arguments with getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hr", ["help", "rss"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    # If no options have been given --rss is the default
    if not opts:
        opts = [("--rss", "")]

    # Install a CookieJar
    cookiejar = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
    urllib2.install_opener(opener)

    # What to do with given options
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-r", "--rss"):
            login(instapaper_username, instapaper_password)
            fetch_via_rss()
            pass

if __name__ == "__main__":
    main()

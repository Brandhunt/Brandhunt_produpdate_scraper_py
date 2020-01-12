

#  /|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\  
# <   -  Brandhunt Product Update Scraper   -   >
#  \|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/


# --- IMPORT SECTION --- #

import scraperwiki
import lxml.html
import os
import requests
import json
import base64
import mysql.connector

from splinter import Browser

#   Connect to Wordpress Site via REST API and get all the proper URLs to be scraped!

wp_username = os.environ['MORPH_WP_USERNAME']
wp_password = os.environ['MORPH_WP_PASSWORD']
wp_connectwp_url = os.environ['MORPH_WP_CONNECT_URL']
wp_connectwp_url_2 = os.environ['MORPH_WP_CONNECT_URL_2']

token = base64.standard_b64encode(wp_username + ':' + wp_password)
headers = {'Authorization': 'Basic ' + token}

#r = requests.post(wp_connectwp_url, headers=headers, json=post)
r = requests.get(wp_connectwp_url, headers=headers)
jsonprods = r.json()

r = requests.get(wp_connectwp_url_2, headers=headers)
jsonwebsites = json.loads(r.content)

#print (json.dumps(jsonwebsites, indent=2))

#print('Your post is published on ' + json.loads(r.content)['link'])
#print('Data found: ' + json.loads(r.content)['link'])
#print('Data found: ' + r.json())

#pretty_json = json.loads(r.content)
#print(json.dumps(pretty_json, indent=2))

#   Decode and handle these URLs!

for product in jsonprods:
    domain = product['domain']
    prodid = product['productid']
    url = product['url']
    
    html = scraperwiki.scrape(url)
    
    #print(prodid)
  
  

#   Connect to database and get the needed information!

##wp_db_name = os.environ['MORPH_DB_NAME']
##wp_db_user = os.environ['MORPH_DB_USER']
##wp_db_password = os.environ['MORPH_DB_PASSWORD']
##wp_db_host = os.environ['MORPH_DB_HOST']

##wp_db_charset = os.environ['MORPH_DB_CHARSET']
##wp_db_collate = ''

##cnx = mysql.connector.connect(user=wp_db_user, 
##                              password=wp_db_password,
##                              host=wp_db_host,
##                              database=wp_db_name)
##cnx.close()

# # Read in a page
# html = scraperwiki.scrape("http://foo.com")
#
# # Find something on the page using css selectors
# root = lxml.html.fromstring(html)
# root.cssselect("div[align='left']")
#
# # Write out to the sqlite database using scraperwiki library
# scraperwiki.sqlite.save(unique_keys=['name'], data={"name": "susan", "occupation": "software developer"})
#
# # An arbitrary query against the database
# scraperwiki.sql.select("* from data where 'name'='peter'")

# You don't have to do things with the ScraperWiki and lxml libraries.
# You can use whatever libraries you want: https://morph.io/documentation/python
# All that matters is that your final data is written to an SQLite database
# called "data.sqlite" in the current working directory which has at least a table
# called "data".


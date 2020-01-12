

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
import re
import sys

from splinter import Browser

# --- FUNCTION SECTION --- #

# *** --- For getting proper value from scraped HTML elements --- *** #
def getmoneyfromtext(price):
    val = re.sub(r'\.(?=.*\.)', '', price.replace(',', '.'))
    if not val: return val
    else: return '{:f}'.format(val)
    
# *** --- For converting scraped price to correct value according to wanted currency --- *** #
def converttocorrectprice(price, currencysymbol):
    
    r = requests.get('https://api.exchangeratesapi.io/latest?base=' + currencysymbol + '', headers=headers)
    jsonrates = r.json()
    foundinrates = false
    
    for ratekey, ratevalue in jsonrates.items():
        if website[priceselector].find('' + ratekey + ''):
            price = price.replace(r'[^0-9,.]', '')
            price = getmoneyfromtext(price)
            price = price / ratevalue
            price = getmoneyfromtext(price)
            foundinrates = true
            break
    
    if not foundinrates:
        if website[priceselector].find('$'):
            price = price.replace(r'[^0-9,.]', '')
            price = getmoneyfromtext(price)
            price = price / jsonrates['USD']
            price = getmoneyfromtext(price)
        elif website[priceselector].find('£'):
            price = price.replace(r'[^0-9,.]', '')
            price = getmoneyfromtext(price)
            price = price / jsonrates['GBP']
            price = getmoneyfromtext(price)
        elif website[priceselector].find('€'):
            price = price.replace(r'[^0-9,.]', '')
            price = getmoneyfromtext(price)
            price = price / jsonrates['EUR']
            price = getmoneyfromtext(price)
        else:
            price = price.replace(r'[^0-9,.]', '')
            price = getmoneyfromtext(price)
            
    return price
    
# --> First, check if the database should be reset:

if bool(os.environ['MORPH_RESET_DB']):
    scraperwiki.sql.execute('TRUNCATE dbdata')

# --> Connect to Wordpress Site via REST API and get all the proper URLs to be scraped!

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

# --> Decode and handle these URLs!

arraus = []

for website in jsonwebsites:
    
    for product in jsonprods:
        
        if website['domain'] == product['domain']:
            
            # --- First, get the HTML for each domain part --- #
            
            if website['scrapetype'] == 'standard_morph_io':
                
                try:
                    # >>> GET THE HTML <<< #
                    html = scraperwiki.scrape(url)

                    # >>> GET THE HTML ROOT <<< #
                    root = lxml.html.fromstring(html)

                    # >>> GET THE PRICE <<< #

                    price_elements = ''
                    price = ''
                    
                    try:
                        if website[priceselector].find('[multiple],'):
                            website[priceselector].replace('[multiple],', '')
                            price_elements = root.cssselect(website[priceselector])

                            for el in price_elements:
                                if not el:
                                    continue
                                price = price + el.text + ' '
                        else:
                            price_elements = root.cssselect(website[priceselector])
                            price = price_elements[0].text

                        if website[pricedelimitertoignore]:
                            if website[pricedelimitertoignore].strip().find(' '):
                                sepdelimiters = website[pricedelimitertoignore].strip().split(' ')
                                for delim in sepdelimiters:
                                    price = re.sub(r'\\' + delim.strip() + '', '', price)
                            else:
                                price = re.sub(r'\\' + website[pricedelimitertoignore].strip() + '', '', price)    

                        if website[currencysymbol]:
                            price = converttocorrectprice(price, website[currencysymbol])
                        else:
                            price = price.replace(r'[^0-9,.]', '')
                            price = getmoneyfromtext(price)
                    except:
                        print("Error when scraping price for product ID " + product['productid'] + ": " + sys.exc_info()[0] + " occured!")
                            
                    # >>> GET THE SALES PRICE <<< #
                    
                    salesprice_elements = ''
                    salesprice = ''
                    
                    if website[salespriceselector]:
                        try:
                            salesprice_elements = root.cssselect(website[salespriceselector])
                            salesprice = salesprice_elements[0].text
                            
                            if website[pricedelimitertoignore]:
                                if website[pricedelimitertoignore].strip().find(' '):
                                    sepdelimiters = website[pricedelimitertoignore].strip().split(' ')
                                    for delim in sepdelimiters:
                                        salesprice = re.sub(r'\\' + delim.strip() + '', '', salesprice)
                                else:
                                    salesprice = re.sub(r'\\' + website[pricedelimitertoignore].strip() + '', '', salesprice)    

                            if website[currencysymbol]:
                                salesprice = converttocorrectprice(salesprice, website[currencysymbol])
                            else:
                                salesprice = salesprice.replace(r'[^0-9,.]', '')
                                salesprice = getmoneyfromtext(salesprice)
                        except:
                            print("Error when scraping sales price for product ID " + product['productid'] + ": " + sys.exc_info()[0] + " occured!")

                    # >>> GET THE DOMAIN MISC. ELEMENTS <<< #
                    
                    domainmisc_array = ''
                    
                    if website[domainmisc]:
                        try:
                            domainmisc_array = re.split('{|}', website[domainmisc])
                            for i in range(0, 10, 2):
                                domainmisc_array[(i + 1)] = root.cssselect(domainmisc_array[(i + 1)])
                        except:
                            print("Error when scraping misc. domain information for product ID " + product['productid'] + ": " + sys.exc_info()[0] + " occured!")
                    
                    # >>> GET THE PRODUCT LOGO URL(S) - IF SUCH EXISTS <<< #
                    
                    
                    
                    # >>> GET THE PRODUCT MISC. ELEMENTS <<< #
                    
                    
                    
                    # >>> CHECK FOR PRODUCT PROPERITES IN TITLE(IF ENABLED) <<< #
                    
                    # >>> GET THE IMAGE URL(S) <<< #
                    
                except:
                    print("Error: " + sys.exc_info()[0] + " occured!")
                    continue
                
            elif website['scrapetype'] == 'phantomjs_morph_io':
                
                try:
                    with Browser("phantomjs") as browser:

                        browser.driver.set_window_size(1920, 1080)
                        browser.visit(product['url'])

                        # submit the search form...
                        ##browser.fill("q", "parliament")
                        ##button = browser.find_by_css("button[type='submit']")
                        ##button.click()

                        # Scrape the data you like...
                        ##links = browser.find_by_css(".search-results .list-group-item")
                        ##for link in links:
                        ##    print link['href']
                except:
                    print("Error: " + sys.exc_info()[0] + " occured!")
                    continue
            else:
                continue
            
            # --- Handle importing prices from product --- #
            
            
            
    



##for product in jsonprods:
##    domain = product['domain']
##    prodid = product['productid']
##    url = product['url']
##    
##    html = scraperwiki.scrape(url)
##    
##    #print(prodid)

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


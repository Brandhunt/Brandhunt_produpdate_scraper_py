

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
from urllib.parse import urljoin

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

# *** --- For grabbing URLs from text-based values/strings --- *** #
def graburls(text, imageonly):
    try:
        imgsuffix = ''
        if imageonly:
            imgsuffix = '\.(gif|jpg|jpeg|png|svg|webp)'
        else:
            imgsuffix = '\.([a-zA-Z0-9\&\.\/\?\:@\-_=#])*'
        
        finalmatches = []
        # --> For URLs without URL encoding characters:
        matches = re.findall(r'((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:\~@\-_=#]+' + imgsuffix + '', text)
        for match in matches[0]:
            finalmatches.append(match)
        # --> For URLs - with - URL encoding characters:
        matches = re.findall(r'((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\\%:\~@\-_=#]+' + imgsuffix + '', text)
        for match in matches[0]:
            finalmatches.append(match)
            
        return list(set(finalmatches)).values()
    except:
        return []
    
# *** --- For converting relative URLs to absolute URLs --- *** #
def reltoabs(relurl, baseurl):
    
      
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
    
    if bool(website[ignorethisone]) == true:
        continue
    
    for product in jsonprods:
        
        if website['domain'] == product['domain']:
            
            # --- First, get the HTML for each domain part --- #
            
            if website['scrapetype'] == 'standard_morph_io':
                
                try:
                    # >>> GET THE HTML <<< #
                    html = ''
                    
                    try:
                        html = scraperwiki.scrape(url)
                    except:
                        print("Error when scraping URL for product ID " + product['productid'] + ": " + sys.exc_info()[0] + " occured!")

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
                            for i in range(0, domainmisc_array.len(), 2):
                                domainmisc_array[(i + 1)] = root.cssselect(domainmisc_array[(i + 1)])
                        except:
                            print("Error when scraping misc. domain information for product ID " + product['productid'] + ": " + sys.exc_info()[0] + " occured!")
                    
                    # >>> GET THE PRODUCT LOGO URL(S) - IF SUCH EXISTS <<< #
                    
                    #prodlog_image_urls = ''
                    #prodlog_image_elements = ''
                    prodlog_image_urls = ''
                    productlogourl = ''
                    #productlogo = ''
                    
                    if website[productlogoselector]:
                        try:
                            prodlog_image_elements = root.cssselect(website[productlogoselector])
                            if prodlog_image_elements:
                                image_dom = ','.join(prodlog_image_elements)
                                prodlog_image_urls = graburls(image_dom, true)
                                
                                if len(prodlog_image_urls) > 0:
                                    for imagekey, imageval in prodlog_image_urls.items():
                                        newimageval = urljoin(product['url'], imageval)
                                        if imageval != newimageval:
                                            prodlog_image_urls[imagekey] = newimageval
                                            imageval = newimageval
                                        if not image.find('//'):
                                            del prodlog_image_urls[imagekey]
                                            continue
                                        if imageval[0:2] == '//':
                                            imageval = 'https:' + imageval
                                            prodlog_image_urls[imagekey] = imageval
                                            
                                productlogourl = prodlog_image_urls[0]
                            else:
                                print("No product logo URLs could be found for product ID " + product['productid'] + "!")
                                
                        except:
                            print("Error when scraping product logo images for product ID " + product['productid'] + ": " + sys.exc_info()[0] + " occured!")
                    
                    # >>> GET THE IMAGE URL(S) <<< #
                    
                    image_urls = ''
                    image_elements = ''
                    image_urls_valid = ''
                    images = ''
                    
                    if website[imageselector] and len(website[imageselector]):
                        try:
                            #image_urls = ''
                            image_elements = root.cssselect(website[imageselector])
                            if image_elements:
                                image_dom = ','.join(image_elements)
                                image_urls = graburls(image_dom, true)
                                
                            if len(image_urls) > 0:
                                for imagekey, imageval in image_urls.items():
                                    newimageval = urljoin(product['url'], imageval)
                                    if imageval != newimageval:
                                        image_urls[imagekey] = newimageval
                                        imageval = newimageval
                                    if not image.find('//') or image.find('blank.'):
                                        del image_urls[imagekey]
                                        continue
                                    if imageval[0:2] == '//':
                                        imageval = 'https:' + imageval
                                        image_urls[imagekey] = imageval
                                image_urls_valid = image_urls.values()
                        except:
                            print("Error when scraping images for product ID " + product['productid'] + ": " + sys.exc_info()[0] + " occured!")
                        
                    # >>> GET THE PRODUCT MISC. ELEMENTS <<< #
                    
                    productmisc_array = re.split('{|}', website[productmisc])
                    
                    # --> Define containers for product attributes
                    
                    product_sizes = ''
                    product_brand = ''
                    product_categories = ''
                    product_colors = ''
                    product_sex = ''

                    product_sizetypes = ''
                    product_sizetypemiscs = ''
                    
                    # --> Define values that will be saved to database once done:
                    
                    sizetypemisc = ''
                    preexistingcurrency = ''
                    notfound = ''
                    soldoutupdatemeta = ''
                    soldouthtmlupdatemeta = ''

                    # --> Get 'em!
                    
                    if website[productmisc]:
                        try:
                            for i in range(0, productmisc_array.len(), 2):
                                # --- Are the sizes belonging to the current product of a a specific misc. size type? --- #
                                if productmisc_array[i] == 'sizetypemisc':
                                    sizetypemisc = productmisc_array[(i + 1)]
                                # --- Are there any pre-existing currencies to apply to the price(s)? --- #
                                if productmisc_array[i] == 'pre_existing_currency':
                                    preexistingcurrency = productmisc_array[(i + 1)]
                                    newprice = ''
                                    newprice = price + productmisc_array[(i + 1)].strip()
                                    if website[currencysymbol]:
                                        newprice.upper()
                                        newprice = converttocorrectprice(newprice, website[currencysymbol])
                                    else:
                                        newprice = newprice.replace(r'[^0-9,.]', '')
                                        newprice = getmoneyfromtext(newprice)
                                    price = newprice
                                    if salesprice != '':
                                        newprice = ''
                                        newprice = price + productmisc_array[(i + 1)].strip()
                                        if website[currencysymbol]:
                                            newprice.upper()
                                            newprice = converttocorrectprice(newprice, website[currencysymbol])
                                        else:
                                            newprice = newprice.replace(r'[^0-9,.]', '')
                                            newprice = getmoneyfromtext(newprice)
                                        salesprice = newprice
                                # --- Should the product skip any URLs(Product logo and normal IMGs) containing any specific string(s)? --- #
                                if productmisc_array[i] == 'skip_img_containing':
                                    if image_urls_valid != '':
                                        for e in range(0, image_urls_valid.len(), 1):
                                            if image_urls_valid[e].find(productmisc_array[(i + 1)]):
                                                del image_urls_valid[e]
                                            images = ','.join(image_urls_valid)
                                    if prodlog_image_urls != '':
                                        for imagekey, imageval in prodlog_image_urls.items():
                                            if imageval.find(productmisc_array[(i + 1)]):
                                                del prodlog_image_urls[imagekey]
                                        productlogourl = prodlog_image_urls[0]       
                                # --- Should we remove the product on 404 Error? --- #
                                ###if productmisc_array[i] == 'allow_remove_on_404':
                                ###   if httpstatus == 404:
                                ###       notfound = 1
                                #pass
                                # --- Use custom domain name(In case any brands doesn't exist for current product) --- #
                                ###if productmisc_array[i] == 'domain_name':
                                ###   brand_array = []
                                ###   productmisc_array[(i + 1)] != '':
                                ###      brand_termus = productmisc_array[(i + 1)].strip()
                                ###      SLUGIFY brand_termus HERE
                                ###      CHECK IF brand_termus ALREADY EXISTS IN REMOTE DB
                                #pass
                                # --- Should the product apply a specific category automatically? --- #
                                ###if productmisc_array[i] == 'add_category':
                                ###   cats_to_add = ','.split(productmisc_array[(i + 1)])
                                ###   cat_result = []
                                ###   for cat in cats_to_add:
                                ###      SLUGIFY cat HERE
                                ###      CHECK IF cat ALREADY EXISTS IN REMOTE DB
                                #pass
                                # --- Should the product apply the male/female attribute automatically? --- #
                                # --- !!! IMPORTANT --> IF THIS SHOULD OVERRIDE OTHER SEX ATTR. IMPORTS, !!! --- #
                                # --- !!! THEN PUT THIS LAST IN ORDER IN PRODUCTMISC. TEXT FIELD BEFORE SCRAPING !!! --- #
                                if productmisc_array[i] == 'is_male':
                                   product_sex = ['Male']
                                elif productmisc_array[i] == 'is_male':
                                    product_sex = ['Female']
                                else:
                                    product_sex = ['Male', 'Female']
                                    
                                # --> Attempt scraping of product misc. elements:
                                
                                prodmisc_backup = productmisc_array[(i+1)].strip().decode('string_escape')
                                #prodmisc_elements = root.cssselect(productmisc_array[(i+1)])
                                productmisc_array[(i+1)] = root.cssselect(productmisc_array[(i+1)])
                                if productmisc_array[(i+1)]:
                                    # --- Has the product got any special sale price applied? --- #
                                    if productmisc_array[i] == 'before_sale_price':
                                        if productmisc_array[(i+1)].len() > 0:
                                            newprice = productmisc_array[(i+1)][0]
                                            if website[currencysymbol]:
                                                newprice.upper()
                                                if website[pricedelimitertoignore]:
                                                    if website[pricedelimitertoignore].strip().find(' '):
                                                        sepdelimiters = website[pricedelimitertoignore].strip().split(' ')
                                                        for delim in sepdelimiters:
                                                            newprice = re.sub(r'\\' + delim.strip() + '', '', newprice)
                                                    else:
                                                        newprice = re.sub(r'\\' + website[pricedelimitertoignore].strip() + '', '', newprice) 
                                                newprice = converttocorrectprice(newprice, website[currencysymbol])
                                            else:
                                                newprice = newprice.replace(r'[^0-9,.]', '')
                                                newprice = getmoneyfromtext(newprice)   
                                            saleprice = price
                                            price = newprice
                                    # --- Get sex attributes from current scrape --- #
                                    ###if productmisc_array[i] == 'pa_sex':
                                    ###   
                                    #pass
                                    # --- Get brand attribute(s) from current scrape --- #
                                    ###
                                    ###
                                    #pass
                                    # --- Get size attributes from current scrape --- #
                                    ###
                                    ###
                                    #pass
                                    # --- Get color attributes from current scrape --- #
                                    ###
                                    ###
                                    #pass
                                    # --- Get categories from current scrape --- #
                                    ###
                                    ###
                                    #pass
                                    # --- Is the product no longer existing - Does the page for it not exist anymore? --- #
                                    if productmisc_array[i] == 'notfound':
                                        if productmisc_array[($i+1)].len() > 0:
                                            notfound = true
                                    # --- Has the product sold out yet? --- #
                                    if productmisc_array[i] == 'sold_out':
                                        if productmisc_array[($i+1)].len() > 0:
                                            soldoutupdatemeta = true
                                            price = '0.0 BUCKS'
											price = price.replace(r'[^0-9,.]', '')
                                            price = getmoneyfromtext(price)
                                        else:
                                            soldoutupdatemeta = false
                                            
                                    # --> Check the HTML if neccessary! Any already existing product attributes found there?
                                    
                                    productmisc_array[(i+1)] = lxml.html.tostring(productmisc_array[(i+1)])
                                    # --- Get sex attributes from current scrape --- #
                                    ###if productmisc_array[i] == 'pa_sex':
                                    ###   
                                    #pass
                                    # --- Get size attribute(s) from current scrape --- #
                                    ###
                                    ###
                                    #pass
                                    # --- Get brand attributes from current scrape --- #
                                    ###
                                    ###
                                    #pass
                                    # --- Get categories from current scrape --- #
                                    ###
                                    ###
                                    #pass
                                    # --- Get color attributes from current scrape --- #
                                    ###
                                    ###
                                    #pass
                                    # --- Has the product sold out yet? --- #
                                    selector_one_string_two = prodmisc_backup.split(',')
									if selector_one_string_two.len() > 1:
                                        productmisc_array[(i+1)] = lxml.html.tostring(selector_one_string_two[0].strip().decode('string_escape'))
										if productmisc_array[($i+1)].find(selector_one_string_two[1]):
											soldouthtmlupdatemeta = true
											price = '0.0 BUCKS'
											price = price.replace(r'[^0-9,.]', '')
                                            price = getmoneyfromtext(price)
										else:
											soldouthtmlupdatemeta = false
                                    # --- Should we skip the first size alternative on information import? --- #
                                    ###
                                    ###
                                    #pass
                                    
                            # --> Fix categories for the product! <-- #
                            ###
                            ###
                            #pass
                            # --> Apply sizetype attributes where needed! <-- #
                            ###
                            ###
                            #pass
                            # --> Fix/correct binds between existing product sizes and sizetypes(Including misc. sizetypes)! <-- #
                            ###
                            ###
                            #pass
                            # --> Apply color, size, sex and brand to the product! <-- #
                            ###
                            ###
                            #pass
                            
                            # --- Make sure to empty all the already-checked bits and join the productmisc. bits back together! --- #
                            ###
                            ###
                            #pass           
                            
                        except:
                            print("Error when scraping misc. product information for product ID " + product['productid'] + ": " + sys.exc_info()[0] + " occured!")

                    # >>> CHECK FOR PRODUCT PROPERITES IN TITLE(IF ENABLED) <<< #
                    
                    if bool(website[lookforprodpropintitle]) == true:
                        try:
                            trythislater = 1
                            ###
                            ###
                            #pass
                        except:
                            print("Error when looking after prod. properties in title for product ID " + product['productid'] + ": " + sys.exc_info()[0] + " occured!")
                    
                    # >>> MAKE PRICES NUMERIC <<< #
                    price =
                    salesprice =
                    
                    # >>> STORE PRODUCT VALUES IN MORPH.IO DATABASE <<< #
                    
                    #HEPP
                    
                except:
                    print("Error: " + sys.exc_info()[0] + " occured!")
                    #STORE PRODUCT IN DATABASE AS SHOULD_DELETE IF HTTP404 ERROR EXISTS
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


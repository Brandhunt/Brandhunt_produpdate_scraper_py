#!/usr/bin/env python
# -*- coding: utf-8 -*- 

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
from slugify import slugify

# --- FUNCTION SECTION --- #

# *** --- Replacement for PHP's array merge functionality --- *** #
def array_merge(array1, array2):
    if isinstance(array1, list) and isinstance(array2, list):
        return array1 + array2
    elif isinstance(array1, dict) and isinstance(array2, dict):
        return dict(list(array1.items()) + list(array2.items()))
    elif isinstance(array1, set) and isinstance(array2, set):
        return array1.union(array2)
    return false

# *** --- For checking if a certain product attribute exists --- *** #
def doesprodattrexist(prodattrlist, term, taxonomy):
    for prodattr in prodattrlist:
        if prodattr['term_id'] == term or prodattr['name'] == term or prodattr['slug'] == term:
            return prodattr
        else:
            return 0
    
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
    pass
      
# --> First, check if the database should be reset:

if bool(os.environ['MORPH_RESET_DB']):
    scraperwiki.sql.execute('TRUNCATE dbdata')

# --> Connect to Wordpress Site via REST API and get all the proper URLs to be scraped!

wp_username = os.environ['MORPH_WP_USERNAME']
wp_password = os.environ['MORPH_WP_PASSWORD']
wp_connectwp_url = os.environ['MORPH_WP_CONNECT_URL']
wp_connectwp_url_2 = os.environ['MORPH_WP_CONNECT_URL_2']
wp_connectwp_url_3 = os.environ['MORPH_WP_CONNECT_URL_3']
wp_connectwp_url_4 = os.environ['MORPH_WP_CONNECT_URL_4']
wp_connectwp_url_5 = os.environ['MORPH_WP_CONNECT_URL_5']

token = base64.standard_b64encode(wp_username + ':' + wp_password)
headers = {'Authorization': 'Basic ' + token}

r = requests.get(wp_connectwp_url, headers=headers)
jsonprods = r.json()

r = requests.get(wp_connectwp_url_2, headers=headers)
jsonwebsites = json.loads(r.content)

r = requests.get(wp_connectwp_url_3, headers=headers)
jsonprodattr = json.loads(r.content)

r = requests.get(wp_connectwp_url_4, headers=headers)
jsoncatsizetypemaps = json.loads(r.content)

r = requests.get(wp_connectwp_url_5, headers=headers)
jsoncatmaps = json.loads(r.content)

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
                    
                    print("Currently scraping product with ID " + product[product_id])

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
                    
                    product_brand = ''
                    product_colors = ''
                    product_sex = ''
                    product_sizes = ''
                    product_sizetypes = ''
                    product_sizetypemiscs = ''
                    product_categories = ''
                    
                    # --> Define values that will be saved to database once done:
                    
                    sizetypemisc = ''
                    preexistingcurrency = ''
                    notfound = ''
                    shouldremoveonnotfound = false
                    soldoutupdatemeta = ''
                    soldouthtmlupdatemeta = ''
                    catstoaddresult = ''
                    attributes_to_store = ''
                    
                    insert_sizetosizetype = ''
                    remove_sizetosizetype = ''
                    insert_sizetosizetypemisc = ''
                    remove_sizetosizetypemisc = ''

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
                                if productmisc_array[i] == 'allow_remove_on_404':
                                    shouldremoveonnotfound = 1
                                # --- Use custom domain name(In case any brands doesn't exist for current product) --- #
                                if productmisc_array[i] == 'domain_name':
                                    brand_array = []
                                    if productmisc_array[(i + 1)] != '':
                                        brand_termus = productmisc_array[(i + 1)].strip()
                                        clean_brand = slugify(brand_termus.strip())
                                        term = doesprodattrexist(jsonprodattr['pa_brand'], brand_termus, 'pa_brand')
                                         #TUPPLE STRUCTURE: (Term(ID/NAME/SLUG), newtermTrue_existingtermFalse)
                                        if term:
                                            brand_array.append((term, false))
                                        else:
                                            term = []
                                            term['term_id'] = -1
                                            term['name'] = brand_termus
                                            term['slug'] = clean_brand
                                            term['taxonomy'] = 'pa_brand'
                                            brand_array.append((term, true))
                                        product_brand = brand_array
                                        productmisc_array[(i+1)] = '.somethingelse'
                                # --- Should the product apply a specific category automatically? --- #
                                if productmisc_array[i] == 'add_category':
                                   cats_to_add = ','.split(productmisc_array[(i + 1)])
                                   cat_result = []
                                   for cat in cats_to_add:
                                      clean_cat = slugify(cat.strip())
                                      term = doesprodattrexist(jsonprodattr['product_cat'], cat, 'product_cat')
                                      #TUPPLE STRUCTURE: (Term(ID/NAME/SLUG), newtermTrue_existingtermFalse, resultcats)
                                      if term:
                                         cat_result.append((term, false))
                                         cat_parents = term['ancestors']
                                         for parent_id in cat_parents:
                                             parent = doesprodattrexist(jsonprodattr['product_cat'], parent_id, 'product_cat')
                                             if not parent in cat_result:
                                                  cat_result.append((parent, false))
                                      else:
                                          term = []
                                          term['term_id'] = -1
                                          term['name'] = cat
                                          term['slug'] = clean_cat
                                          term['taxonomy'] = 'product_cat'
                                          cat_result.append((term, true))
                                   catstoaddresult = cat_result
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
                                    if productmisc_array[i] == 'pa_sex':
                                        if productmisc_array[(i+1)].len() > 0:
                                            sex_array = []
                                            for sex_termus in productmisc_array[(i+1)]:
                                                clean_sex = sex_termus.strip()
                                                term = doesprodattrexist(jsonprodattr['pa_sex'], sex_termus, 'pa_sex')
                                                #TUPPLE STRUCTURE: (Term(ID/NAME/SLUG), newtermTrue_existingtermFalse)
                                                if term:
                                                    sex_array.append((term, false))
                                                else:
                                                    term = []
                                                    term['term_id'] = -1
                                                    term['name'] = sex_termus
                                                    term['slug'] = clean_sex
                                                    term['taxonomy'] = 'pa_sex'
                                                    sex_array.append((term, true))
                                            product_sex = sex_array
                                    # --- Get brand attribute(s) from current scrape --- #
                                    if productmisc_array[i] == 'pa_brand':
                                        brand_array = []
                                        if productmisc_array[(i+1)].len() > 0:
                                            brand_termus = productmisc_array[(i+1)][0]
                                            clean_brand = slugify(brand_termus.strip())
                                            term = doesprodattrexist(jsonprodattr['pa_brand'], brand_termus, 'pa_brand')
                                            # TUPPLE STRUCTURE: (Term(ID/NAME/SLUG), newtermTrue_existingtermFalse)
                                            if term:
                                                brand_array.append((term, false))
                                            else:
                                                term = []
                                                term['term_id'] = -1
                                                term['name'] = brand_termus
                                                term['slug'] = clean_brand
                                                term['taxonomy'] = 'pa_brand'
                                                brand_array.append((term, true))
                                            product_brand = brand_array
                                    # --- Get size attributes from current scrape --- #
                                    if productmisc_array[i] == 'pa_size':
                                        if productmisc_array[(i+1)].len() > 0:
                                            size_array = []
                                            for size_termus in productmisc_array[(i+1)]:
                                                output = re.search(r'\(.*Only.*\)|\(.*Out.*\)|\(.*In.*\)|\(.*Lager.*\)', size_termus, flags=re.IGNORECASE)
                                                output2 = re.search(r'.*Bevaka.*', size_termus, flags=re.IGNORECASE)
                                                output3 = re.search(r'.*Stock.*', size_termus, flags=re.IGNORECASE)
                                                output4 = re.search(r'.*Size\s+\d+.*', size_termus, flags=re.IGNORECASE)
                                                if output is not None:
                                                    size_termus = re.sub(r'\(.*\)', '', size_termus, flags=re.IGNORECASE)
                                                elif output2 is not None:
                                                    size_termus = re.sub(r'\s+-\s+Bevaka.*', '', size_termus, flags=re.IGNORECASE)
                                                elif output3 is not None:
                                                    size_termus = re.sub(r'\s+-\s+.*Stock.*', '', size_termus, flags=re.IGNORECASE)
                                                elif output4 is not None:
                                                    size_termus = re.sub(r'.*Size\s+', '', size_termus, flags=re.IGNORECASE)
                                                size_termus = size_termus.replace(' ', '')
                                                clean_size = slugify(size_termus.strip())
                                                term = doesprodattrexist(jsonprodattr['pa_size'], size_termus, 'pa_size')
                                                if term:
                                                    size_array.append((term, false))
                                                else:
                                                    term = []
                                                    term['term_id'] = -1
                                                    term['name'] = size_termus
                                                    term['slug'] = clean_size
                                                    term['taxonomy'] = 'pa_size'
                                                    size_array.append((term, true))
                                            product_sizes = size_array
                                    # --- Get color attributes from current scrape --- #
                                    if productmisc_array[i] == 'pa_color':
                                        if productmisc_array[(i+1)].len() > 0:
                                            color_array = []
                                            for color_termus in productmisc_array[(i+1)]:
                                                clean_color = slugify(color_termus.strip())
                                                term = doesprodattrexist(jsonprodattr['pa_color'], color_termus, 'pa_color')
                                                if term:
                                                    color_array.append((term, false))
                                                else:
                                                    term = []
                                                    term['term_id'] = -1
                                                    term['name'] = color_termus
                                                    term['slug'] = clean_color
                                                    term['taxonomy'] = 'pa_color'
                                                    color_array.append((term, true))
                                            product_colors = color_array
                                    # --- Get categories from current scrape --- #
                                    if productmisc_array[i] == 'pa_category':
                                        if productmisc_array[(i+1)].len() > 0:
                                            category_array = []
                                            for cat_termus in productmisc_array[(i+1)]:
                                                clean_cat = slugify(cat_termus.strip())
                                                term = doesprodattrexist(jsonprodattr['product_cat'], cat_termus, 'product_cat')
                                                if term:
                                                    category_array.append((term, false))
                                                    cat_parents = term['ancestors']
                                                    for parent_id in cat_parents:
                                                        parent = doesprodattrexist(jsonprodattr['product_cat'], parent_id, 'product_cat')
                                                        if not parent in category_array:
                                                            category_array.append((parent, false))
                                                else:
                                                    term = []
                                                    term['term_id'] = -1
                                                    term['name'] = cat_termus
                                                    term['slug'] = clean_cat
                                                    term['taxonomy'] = 'product_cat'
                                                    category_array.append((term, true))
                                            product_categories = category_array
                                    # --- Is the product no longer existing - Does the page for it not exist anymore? --- #
                                    if productmisc_array[i] == 'notfound':
                                        if productmisc_array[(i+1)].len() > 0:
                                            notfound = true
                                    # --- Has the product sold out yet? --- #
                                    if productmisc_array[i] == 'sold_out':
                                        if productmisc_array[(i+1)].len() > 0:
                                            soldoutupdatemeta = true
                                            price = '0.0 BUCKS'
                                            price = price.replace(r'[^0-9,.]', '')
                                            price = getmoneyfromtext(price)
                                        else:
                                            soldoutupdatemeta = false
                                            
                                    # --> Check the HTML if neccessary! Any already existing product attributes found there?
                                    
                                    productmisc_array[(i+1)] = lxml.html.tostring(productmisc_array[(i+1)])
                                    # --- Get sex attributes from current scrape --- #
                                    if productmisc_array[i] == 'pa_sex_html':
                                        sexies = jsonprodattr['pa_sex']
                                        sexies_result = []
                                        for sexterm in sexies:
                                            term_name = sexterm['name']
                                            sex_html = productmisc_array[(i+1)]
                                            if sex_html.upper().find(term_name.upper()):
                                                term = doesprodattrexist(jsonprodattr['pa_sex'], sexterm['term_id'], 'pa_sex')
                                                if term:
                                                    sexies_result.append((term, false))
                                        product_sex = sexies_result
                                    # --- Get size attribute(s) from current scrape --- #
                                    if productmisc_array[i] == 'pa_size_html':
                                        sizies = jsonprodattr['pa_size']
                                        sizies_result = []
                                        for sizeterm in sizies:
                                            term_name = sizeterm['name']
                                            size_html = productmisc_array[(i+1)]
                                            output = re.search(r'\(.*Only.*\)|\(.*Out.*\)|\(.*In.*\)|\(.*Lager.*\)', size_html, flags=re.IGNORECASE)
                                            output2 = re.search(r'.*Bevaka.*', size_html, flags=re.IGNORECASE)
                                            output3 = re.search(r'.*Stock.*', size_html, flags=re.IGNORECASE)
                                            output4 = re.search(r'.*Size\s+\d+.*', size_html, flags=re.IGNORECASE)
                                            if output is not None:
                                                size_html = re.sub(r'\(.*\)', '', size_html, flags=re.IGNORECASE)
                                            elif output2 is not None:
                                                size_html = re.sub(r'\s+-\s+Bevaka.*', '', size_html, flags=re.IGNORECASE)
                                            elif output3 is not None:
                                                size_html = re.sub(r'\s+-\s+.*Stock.*', '', size_html, flags=re.IGNORECASE)
                                            elif output4 is not None:
                                                size_html = re.sub(r'.*Size\s+', '', size_html, flags=re.IGNORECASE)
                                            if size_html.upper().find(term_name.upper()):
                                                term = doesprodattrexist(jsonprodattr['pa_sex'], sexterm['term_id'], 'pa_sex')
                                                if term:
                                                    sexies_result.append((term, false))
                                        if sizies_result:
                                            if product_sizes == '':
                                                product_sizes = sizies_result
                                            else:
                                                product_sizes = array_merge(product_sizes, sizies_result)
                                    # --- Get brand attributes from current scrape --- #
                                    if productmisc_array[i] == 'pa_brand_html':
                                        brandies = jsonprodattr['pa_brand']
                                        brandies_result = []
                                        for brandterm in brandies:
                                            term_name = brandterm['name']
                                            brand_html = productmisc_array[(i+1)]
                                            if brand_html.upper().find(term_name.upper()):
                                                term = doesprodattrexist(jsonprodattr['pa_brand'], brandterm['term_id'], 'pa_brand')
                                                if term:
                                                    brandies_result.append((term, false))
                                        if brandies_result:
                                            if product_brand == '':
                                                product_brand = brandies_result
                                            else:
                                                product_brand = array_merge(product_brand, brandies_result)
                                    # --- Get categories from current scrape --- #
                                    if productmisc_array[i] == 'pa_category_html':
                                        caties = jsonprodattr['product_cat']
                                        caties_result = []
                                        for catterm in caties:
                                            term_name = catterm['name']
                                            cat_html = productmisc_array[(i+1)]
                                            if cat_html.upper().find(term_name.upper()):
                                                term = doesprodattrexist(jsonprodattr['product_cat'], catterm['term_id'], 'product_cat')
                                                if term:
                                                    caties_result.append((term, false))
                                                    cat_parents = term['ancestors']
                                                    for parent_id in cat_parents:
                                                        parent = doesprodattrexist(jsonprodattr['product_cat'], parent_id, 'product_cat')
                                                        if not parent in caties_result:
                                                            caties_result.append((parent, false))
                                        if caties_result:
                                            if product_categories == '':
                                                product_categories = caties_result
                                            else:
                                                product_categories = array_merge(product_categories, caties_result)
                                    # --- Get color attributes from current scrape --- #
                                    if productmisc_array[i] == 'pa_color_html':
                                        colories = jsonprodattr['pa_color']
                                        colories_result = []
                                        for colorterm in colories:
                                            term_name = colorterm['name']
                                            color_html = productmisc_array[(i+1)]
                                            if color_html.upper().find(term_name.upper()):
                                                term = doesprodattrexist(jsonprodattr['pa_color'], colorterm['term_id'], 'pa_color')
                                                if term:
                                                    colories_result.append((term, false))
                                        if colories_result:
                                            if product_colors == '':
                                                product_colors = colories_result
                                            else:
                                                product_colors = array_merge(product_colors, colories_result)
                                    # --- Has the product sold out yet? --- #
                                    if productmisc_array[i] == 'sold_out_html':
                                        selector_one_string_two = prodmisc_backup.split(',')
                                        if selector_one_string_two.len() > 1:
                                            productmisc_array[(i+1)] = lxml.html.tostring(selector_one_string_two[0].strip().decode('string_escape'))
                                            if productmisc_array[(i+1)].find(selector_one_string_two[1]):
                                                soldouthtmlupdatemeta = true
                                                price = '0.0 BUCKS'
                                                price = price.replace(r'[^0-9,.]', '')
                                                price = getmoneyfromtext(price)
                                            else:
                                                soldouthtmlupdatemeta = false
                                    # --- Should we skip the first size alternative on information import? --- #
                                    if productmisc_array[i] == 'skip_first_size':
                                        if product_sizes != '':
                                            removed_size = product_sizes.pop(0)
                                                    
                            # --> Fix categories for the product! <-- #
                            if product_categories:
                                existing_categories = product['category_ids']
                                if existing_categories:
                                    count = 0
                                    for cat in existing_categories:
                                        term = doesprodattrexist(jsonprodattr['product_cat'], cat, 'product_cat')
                                        existing_categories[count] = ((term, false))
                                        count+=1
                                    product_categories = product_categories + existing_categories   
                                #SAVE CAT. IDS AND PRODUCT HERE IN REMOTE SITE
                            
                            # --> Apply sizetype attributes where needed! <-- #
                            product_sizetypemiscname = sizetypemisc
                            if product_categories != '':
                                array_catsizetypemaps = jsoncatsizetypemaps
                                array_sizetypes = []
                                for catsizetypemap in array_catsizetypemaps:
                                    finalcatsizetypes = catsizetypemap['finalcatsizetype'].split(',')
                                    catstosizetypes = catsizetypemap['catstosizetype'].split(',')
                                    product_category_names = []
                                    matching_cats = []
                                    for cat in product_categories:
                                        category_to_cast_id = cat['term_id']
                                        term = doesprodattrexist(jsonprodattr['product_cat'], category_to_cast_id, 'product_cat')
                                        if term:
                                            product_category_names.append(term['name'])
                                    for catstosizetype in catstosizetypes:
                                        matching_cats = array_merge(matching_cats, filter(lambda x: re.findall(u'(\b.*' + catstosizetype.strip + '\b)', x, flags=re.IGNORECASE), product_category_names))
                                    if matching_cats:
                                        size_type_terms = jsonprodattr['pa_sizetype']
                                        count = 0
                                        for size_type_term in size_type_terms:
                                            size_type_terms[count] = size_type_term['name']
                                            count+=1
                                        filtered_terms = []
                                        for finalcatsizetype in finalcatsizetypes:
                                            filtered_terms = array_merge(filtered_terms, filter(lambda x: re.findall(u'(\b.*' + finalcatsizetype.strip + '\b)', x, flags=re.IGNORECASE), size_type_terms))
                                        for filt_term in filtered_terms:
                                            term = doesprodattrexist(jsonprodattr['pa_sizetype'], filt_term, 'pa_sizetype')
                                            if term:
                                                array_sizetypes.append((term, false))     
                                product_sizetypes = array_sizetypes
                                if not product_sizetypes and product_sizes and not product_sizetypemiscname:
                                    product_sizetypemiscname = 'Other'
                            else:
                                if product_sizes and not wc_product_sizetypemiscname:
                                    product_sizetypemiscname = 'Other'
                            if product_sizetypemiscname:
                                product_sizetypemiscs = []
                                term = doesprodattrexist(jsonprodattr['pa_sizetypemisc'], product_sizetypemiscname, 'pa_sizetypemisc')
                                if term:
                                    product_sizetypemiscs.append((term, false))
                                else:
                                    term = []
                                    term['term_id'] = -1
                                    term['name'] = product_sizetypemiscname.strip()
                                    term['slug'] = product_sizetypemiscname.strip().lower()
                                    term['taxonomy'] = 'pa_sizetypemisc'
                                    product_sizetypemiscs.append((term, true))
                                    
                            # --> Fix/correct binds between existing product sizes and sizetypes(Including misc. sizetypes)! <-- #
                            if product_sizetypes and product_sizes:
                                sizeid_col = product['sizetosizetypemaps']['size']
                                sizetypeid_col = product['sizetosizetypemaps']['sizetype']
                                count = 0
                                for sizeid in sizeid_col:
                                    sizeid_col[count] = doesprodattrexist(jsonprodattr['pa_size'], sizeid, 'pa_size')
                                    count+=1
                                count = 0
                                for sizetypeid in sizetypeid_col:
                                    sizetypeid_col[count] = doesprodattrexist(jsonprodattr['pa_sizetype'], sizetypeid, 'pa_sizetype')
                                    count+=1
                                #SAVE VALUES FOR INSERT
                                compare_sizeid = list(set(product_sizes) - set(sizeid_col))
                                compare_sizetypeid = list(set(product_sizetypes) - set(sizetypeid_col))
                                if compare_sizetypeid and compare_sizeid:
                                    for sizetypeid_insert in compare_sizetypeid:
                                        count = 0
                                        for sizeid_insert in compare_sizeid:
                                            insert_sizetosizetype[count] = (sizeid_insert, sizetypeid_insert, product['productid'])
                                            count+=1
                                #SAVE VALUES FOR REMOVAL
                                compare_sizeid = list(set(sizeid_col) - set(product_sizes))
                                compare_sizetypeid = list(set(sizetypeid_col) - set(product_sizetypes))
                                if compare_sizetypeid and compare_sizeid:
                                    for sizetypeid_remove in compare_sizetypeid:
                                        count = 0
                                        for sizeid_remove in compare_sizeid:
                                            remove_sizetosizetype[count] = (sizeid_remove, sizetypeid_remove, product['productid'])
                                            count+=1   
                                            
                            if product_sizetypemiscs and product_sizes:
                                sizeid_col = product['sizetosizetypemaps']['size_misc']
                                compare_sizetypemiscid = product['sizetosizetypemaps']['sizetype_misc'] 
                                count = 0
                                for sizeid in sizeid_col:
                                    sizeid_col[count] = doesprodattrexist(jsonprodattr['pa_size'], sizeid, 'pa_size')
                                    count+=1
                                count = 0
                                for sizetypemiscid in compare_sizetypemiscid:
                                    compare_sizetypemiscid[count] = doesprodattrexist(jsonprodattr['pa_sizetypemisc'], sizetypemiscid, 'pa_sizetypemisc')
                                    count+=1
                                #SAVE VALUES FOR INSERT
                                compare_sizeid = list(set(product_sizes) - set(sizeid_col))
                                compare_sizetypemiscid = list(set(product_sizetypemiscs) - set(compare_sizetypemiscid)) 
                                if compare_sizetypemiscid and compare_sizeid:
                                    for sizetypemiscid_insert in compare_sizetypemiscid:
                                        count = 0
                                        for sizeid_insert in compare_sizeid:
                                            insert_sizetosizetypemisc[count] = (sizeid_insert, sizetypemiscid_insert, product['productid'])
                                            count+=1
                                #SAVE VALUES FOR REMOVAL
                                compare_sizeid = list(set(sizeid_col) - set(product_sizes))
                                compare_sizetypemiscid = list(set(compare_sizetypemiscid) - set(product_sizetypemiscs))
                                if compare_sizetypemiscid and compare_sizeid:
                                    for sizetypemiscid_remove in compare_sizetypemiscid:
                                        count = 0
                                        for sizeid_remove in compare_sizeid:
                                            remove_sizetosizetypemisc[count] = (sizeid_remove, sizetypemiscid_remove, product['productid'])
                                            count+=1
                            
                            # --> Apply color, size, sex and brand to the product! (Filter the attributes before save)
                            # --> (Filter the attributes before database save)
                            attributes = []
                            attribute_pos = 1 
                            if product_brand:
                                brand_values = product['attributes']['brand']
                                if brand_values:
                                    existing_brands = re.split(',\s*', brand_values)
                                    count = 0
                                    for brand in existing_brands:
                                        existing_brands[count] = (brand, false)
                                        count+=1
                                    product_brand = product_brand + existing_brands
                                attributes.append(['name':'Brand', 'options':product_brand, 'position':attribute_pos, 'visible':1, 'variation':1])
                                attribute_pos+=1
                            if product_colors:
                                color_values = product['attributes']['color']
                                if color_values:
                                    existing_colors = re.split(',\s*', color_values)
                                    count = 0
                                    for color in existing_colors:
                                        existing_colors[count] = (color, false)
                                        count+=1
                                    product_colors = product_colors + existing_colors
                                attributes.append(['name':'Color', 'options':product_colors, 'position':attribute_pos, 'visible':1, 'variation':1])
                                attribute_pos+=1
                            if product_sex:
                                sex_values = product['attributes']['sex']
                                if sex_values:
                                    existing_sex = re.split(',\s*', sex_values)
                                    count = 0
                                    for sex in existing_sex:
                                        existing_sex[count] = (sex, false)
                                        count+=1
                                    product_sex = product_sex + existing_sex
                                attributes.append(['name':'Sex', 'options':product_sex, 'position':attribute_pos, 'visible':1, 'variation':1])
                                attribute_pos+=1
                            if product_sizes:
                                size_values = product['attributes']['size']
                                if size_values:
                                    existing_sizes = re.split(',\s*', size_values)
                                    count = 0
                                    for size in existing_sizes:
                                        existing_sizes[count] = (size, false)
                                        count+=1
                                    product_sizes = product_sizes + existing_sizes
                                attributes.append(['name':'Size', 'options':product_sizes, 'position':attribute_pos, 'visible':1, 'variation':1])
                                attribute_pos+=1
                            if product_sizetypes:
                                sizetype_values = product['attributes']['sizetype']
                                if sizetype_values:
                                    existing_sizetypes = re.split(',\s*', sizetype_values)
                                    count = 0
                                    for sizetype in existing_sizetypes:
                                        existing_sizetypes[count] = (sizetype, false)
                                        count+=1
                                    product_sizetypes = product_sizetypes + existing_sizetypes
                                attributes.append(['name':'Sizetype', 'options':product_sizetypes, 'position':attribute_pos, 'visible':1, 'variation':1])
                                attribute_pos+=1
                            if product_sizetypemiscs:
                                sizetypemisc_values = product['attributes']['sizetypemisc']
                                if sizetypemisc_values:
                                    existing_sizetypemiscs = re.split(',\s*', sizetypemisc_values)
                                    count = 0
                                    for sizetypemisc in existing_sizetypemiscs:
                                        existing_sizetypemiscs[count] = (sizetypemisc, false)
                                        count+=1
                                    product_sizetypemiscs = product_sizetypemiscs + existing_sizetypemiscs
                                attributes.append(['name':'Sizetypemisc', 'options':product_sizetypemiscs, 'position':attribute_pos, 'visible':1, 'variation':1])
                                attribute_pos+=1
                            attributes_to_store = attributes
                            # --- Make sure to empty all the already-checked bits and join the productmisc. bits back together! --- #
                            ###
                            ###
                            #pass
                        except:
                            print("Error when scraping misc. product information for product ID " + product['productid'] + ": " + sys.exc_info()[0] + " occured!")

                    # >>> CHECK FOR PRODUCT PROPERITES IN TITLE(IF ENABLED) <<< #
                    
                    if bool(website[lookforprodpropintitle]) == true:
                        try:
                            termies = []
                            termies[0] = jsonprodattr['pa_brand']
                            termies[1] = jsonprodattr['pa_color']
                            termies[2] = jsonprodattr['pa_sex']
                            termies_result = [[], [], []]
                            for i in range(3):
                                for term in termies[i]:
                                    term_name = term['name']
                                    product_name = product['name']
                                    if product_name.upper().find(term_name.upper()):
                                        termies_result[i].append(doesprodattrexist(jsonprodattr[term['taxonomy']], term['term_id'], term['taxonomy']), false)
                            attributes = []
                            attribute_pos = 1
                            if termies_result[0]:
                                brand_values = product_brand
                                if brand_values:
                                    existing_brands = re.split(',\s*', brand_values)
                                    '''count = 0
                                    for brand in existing_brands:
                                        existing_brands[count] = (brand, false)
                                        count+=1'''
                                    termies_result[0] = array_merge(termies_result[0], existing_brands)
                                attributes.append(['name':'Brand', 'options':termies_result[0], 'position':attribute_pos, 'visible':1, 'variation':1])
                                attribute_pos+=1
                            else:
                                brand_values = product_brand
                                if brand_values:
                                    existing_brands = re.split(',\s*', brand_values)
                                    '''count = 0
                                    for brand in existing_brands:
                                        existing_brands[count] = (brand, false)
                                        count+=1'''
                                    product_brand = existing_brands
                                    attributes.append(['name':'Brand', 'options':product_brand, 'position':attribute_pos, 'visible':1, 'variation':1])
                                    attribute_pos+=1
                            if termies_result[1]:
                                color_values = product_colors
                                if color_values:
                                    existing_colors = re.split(',\s*', color_values)
                                    '''count = 0
                                    for color in existing_colors:
                                        existing_colors[count] = (color, false)
                                        count+=1'''
                                    termies_result[1] = array_merge(termies_result[1], existing_colors)
                                attributes.append(['name':'Color', 'options':termies_result[1], 'position':attribute_pos, 'visible':1, 'variation':1])
                                attribute_pos+=1
                            else:
                                color_values = product_colors
                                if color_values:
                                    existing_colors = re.split(',\s*', color_values)
                                    '''count = 0
                                    for color in existing_colors:
                                        existing_colors[count] = (color, false)
                                        count+=1'''
                                    product_colors = existing_colors
                                    attributes.append(['name':'Brand', 'options':product_colors, 'position':attribute_pos, 'visible':1, 'variation':1])
                                    attribute_pos+=1
                            if termies_result[2]:
                                sex_values = product_sex
                                if sex_values:
                                    existing_sex = re.split(',\s*', sex_values)
                                    '''count = 0
                                    for sex in existing_sex:
                                        existing_sex[count] = (sex, false)
                                        count+=1'''
                                    termies_result[2] = array_merge(termies_result[2], existing_sex)
                                attributes.append(['name':'Sex', 'options':termies_result[2], 'position':attribute_pos, 'visible':1, 'variation':1])
                                attribute_pos+=1
                            else:
                                sex_values = product_sex
                                if sex_values:
                                    existing_sex = re.split(',\s*', sex_values)
                                    '''count = 0
                                    for sex in existing_sex:
                                        existing_sex[count] = (sex, false)
                                        count+=1'''
                                    product_sex = existing_sex
                                    attributes.append(['name':'Sex', 'options':product_sex, 'position':attribute_pos, 'visible':1, 'variation':1])
                                    attribute_pos+=1
                            size_values = product_sizes
                            if size_values:
                                existing_sizes = re.split(',\s*', size_values)
                                product_sizes = existing_sizes
                                attributes.append(['name':'Size', 'options':product_sizes, 'position':attribute_pos, 'visible':1, 'variation':1])
                                attribute_pos+=1
                            sizetype_values = product_sizetypes
                            if sizetype_values:
                                existing_sizetypes = re.split(',\s*', sizetype_values)
                                product_sizetypes = existing_sizetypes
                                attributes.append(['name':'Size', 'options':product_sizetypes, 'position':attribute_pos, 'visible':1, 'variation':1])
                                attribute_pos+=1
                            sizetypemisc_values = product_sizetypemiscs
                            if sizetypemisc_values:
                                existing_sizetypemiscs = re.split(',\s*', sizetypemisc_values)
                                product_sizetypemiscs = existing_sizetypemiscs
                                attributes.append(['name':'Size', 'options':product_sizetypemiscs, 'position':attribute_pos, 'visible':1, 'variation':1])
                                attribute_pos+=1
                            attributes_to_store = attributes
                            category_terms = jsonprodattr['product_cat']
                            category_result = []
                            for term in category_terms:
                                term_name = term['name']
                                product_name = product['name']
                                array_categorymaps = jsoncatmaps
                                if array_categorymaps:
                                    if hasattr(array_categorymaps, term_name):
                                        infliction_array = jsoncatmaps[term_name]['catinflections'].split(',')
                                        for infliction in infliction_array:
                                            if product_name.upper().find(infliction.upper()):
                                                term = doesprodattrexist(jsonprodattr['product_cat'], term['term_id'], 'product_cat')
                                                if term:
                                                    category_result.append((term, false))
                                                 cat_parents = term['ancestors']
                                                 for parent_id in cat_parents:
                                                     parent = doesprodattrexist(jsonprodattr['product_cat'], parent_id, 'product_cat')
                                                     if not parent in category_result:
                                                          category_result.append((parent, false))
                                if product_name.upper().find(term_name.upper()):
                                    term = doesprodattrexist(jsonprodattr['product_cat'], term['term_id'], 'product_cat')
                                        if term:
                                            category_result.append((term, false))
                                         cat_parents = term['ancestors']
                                         for parent_id in cat_parents:
                                             parent = doesprodattrexist(jsonprodattr['product_cat'], parent_id, 'product_cat')
                                             if not parent in category_result:
                                                  category_result.append((parent, false))
                                if category_result:
                                    existing_categories = product['category_ids']
                                    if existing_categories:
                                        category_result = array_merge(category_result, existing_categories)
                                catstoaddresult = cat_result
                                
                        except:
                            print("Error when looking after prod. properties in title for product ID " + product['productid'] + ": " + sys.exc_info()[0] + " occured!")                    
                    
                    # >>> MAKE PRICES NUMERIC <<< #
                    price = getmoneyfromtext(price)
                    salesprice = getmoneyfromtext(salesprice)
                    
                    # >>> STORE PRODUCT VALUES IN MORPH.IO DATABASE <<< #
                    scraperwiki.sqlite.save(unique_keys=['productid'],
                                            data={'domain': "product['domain'],
                                                  'url': product['url'],
                                                  'productid': product['productid'],
                                                  'price': price,
                                                  'salesprice': salesprice,
                          'domainmisc': domainmisc_array,
                          'prodlogurls': prodlog_image_urls,
                          'prodlogurl': productlogourl,
                          'finalimgurls': images,
                          'validimgurls': image_urls_valid,
                          'imgurls': image_urls,
                          'notfound': shouldremoveonnotfound,
                          'soldoutfix': soldoutupdatemeta,
                          'soldouthtmlfix': soldouthtmlupdatemeta,
                          'catstoaddresult': catstoaddresult
                          'attributes': attributes_to_store
                          'sizetypemapsqls': [insert_sizetosizetype,
                                     remove_sizetosizetype,
                                     insert_sizetosizetypemisc,
                                     remove_sizetosizetypemisc])
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

# # An arbitrary query against the database
# scraperwiki.sql.select("* from data where 'name'='peter'")

# You don't have to do things with the ScraperWiki and lxml libraries.
# You can use whatever libraries you want: https://morph.io/documentation/python
# All that matters is that your final data is written to an SQLite database
# called "data.sqlite" in the current working directory which has at least a table
# called "data".


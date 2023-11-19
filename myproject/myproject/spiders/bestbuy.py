import scrapy
import sys
sys.path.append('/home/jon/Desktop/myproject')
from myproject.utils.math_functions import extract_float_from_text, calculate_percentage_difference 
import re
import random

#this spider iterates through all bestbuy product pages by category
class BestbuyPySpider(scrapy.Spider):
    name = 'bestbuy.py'
    allowed_domains = ['bestbuy.com']
    category_ids = {
        'COMPUTERS and TABLETS': 'abcat0500000',
        'APPLIANCES': 'abcat0900000',
        'TV and HOME THEATER': 'abcat0100000',
        'CELLPHONES': 'abcat0800000',
        'AUDIO': 'abcat0200000',
        'VIDEO GAMES': 'abcat0700000',
        'CAMERAS, CAMCORDERS and DRONES': 'abcat0400000',
        'HOME, FURNITURE and OFFICE': 'pcmcat312300050015',
        'SMART HOME, SECURITY and WIFI': 'pcmcat254000050002',
        'CAR ELECTRONICS and GPS': 'abcat0300000',
        'MOVIES and MUSIC': 'abcat0600000',
        'WEARABLE TECHNOLOGY': 'pcmcat332000050000',
        'HEALTH, WELLNESS, FITNESS': 'pcmcat242800050021',
        'OUTDOOR LIVING': 'pcmcat179100050006',
        'TOYS, GAMES and COLLECTIBLES': 'pcmcat252700050006',
        'ELECTRIC TRANSPORTATION': 'pcmcat250300050003',
    }
    user_agents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
               '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
               '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
               'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
               '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', ]
    headers = {
        'User-Agent': random.choice(user_agents), 'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.bestbuy.com/'}
    def start_requests(self):

        for category_name, category_id in self.category_ids.items():
            url = f'https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&browsedCategory={category_id}&id=pcat17071&iht=n&ks=960&list=y&sc=Global&st=categoryid%24{category_id}&type=page&usc=All%20Categories'
            yield scrapy.Request(url=url, headers=self.headers, callback=self.parse, meta={'category_name': category_name})
    


    def parse(self, response):
        product_list = []
        item = {'Website': None,
           'Category': None,
           'Title': None,
           'Old_Price': None,
           'New_Price': None,
           'Discount': None,
           'UPC': None,
           'Link': None}
        products = response.css('li.sku-item')
        next_button = response.css('a.sku-list-page-next')
        if products:
            for product in products:
                #title and pricing
                price_element = product.css('div.priceView-hero-price.priceView-customer-price')
                price = price_element.css('span').css('::text').get()

                 #if a red clearance tag is found, this will execute
                clearance = product.css('div.pricing-price__regular-price::text').get()
                if clearance:
                    #product info: title, price, link, discount
                    title = product.css('a::text').get()
                    href = product.css('a::attr(href)').get()
                    link = f'https://www.bestbuy.com{href}'
                    old_price = extract_float_from_text(str(clearance))
                    new_price = extract_float_from_text(price)
                    discount = calculate_percentage_difference(old_price, new_price)

                    #formulate data to be sent to pipelines
                    item['Website'] = 'BestBuy'
                    item['Category'] = response.meta['category_name']
                    item['Title'] = title
                    item['Old_Price'] = old_price
                    item['New_Price'] = new_price
                    item['Discount'] = discount
                    item['Link'] = link
                    item['UPC'] = None
                    yield scrapy.Request(url=link, headers=self.headers, callback=self.parse_upc, meta={'item': item})
                    
            
            if next_button:
                next_page_href = next_button.css('::attr(href)').get()
                page_link = f'https://www.bestbuy.com{next_page_href}'
                yield scrapy.Request(url=page_link, headers=self.headers, callback=self.parse, meta={'category_name': response.meta['category_name']})
            else:
                print('Last page')

        else:
            raise AttributeError('Page did not load correctly')
        
    def get_upc(self,link,item):
        return scrapy.Request(url=link, headers=self.headers, callback=self.parse_upc, meta={'item' : item, 'link': link})

    def parse_upc(self, response):
        specs_element = response.css('[id*=shop-specifications]')
        script_tags = specs_element.css('script').getall()
        upc_value = None

        for script_tag in script_tags:
            if 'UPC' in script_tag:
                pattern = r'\b\d{12}\b'
                match = re.search(pattern, str(script_tag))
                if match:
                    upc_value = match.group()
                    break

        # Update the UPC value in the item
        item = response.meta['item']
        item['UPC'] = upc_value

        # Yield the item with the updated UPC
        yield item
        return upc_value



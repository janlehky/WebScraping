import scrapy
import re
from scrapy.loader import ItemLoader
from WebScraper.items import Advert

class AdvertSpider(scrapy.Spider):
    name = "adverts"
    start_urls = [
        'http://www.nehnutelnosti.sk/senica/predaj',
    ]

    def parse(self, response):
        # follow links to author pages
        # print('Parse started' + response.url)

        for href in response.css('div.advertisement-head  h2 a::attr(href)').extract():
            # read links on web page and scrape data from them
            yield scrapy.Request(response.urljoin(href),
                                 callback=self.parse_advert)

        # follow pagination links
        # next_page = response.css('div.withLeftBox a.next::attr(href)').extract_first()
        # if next_page is not None:
        #     print(next_page)
        #     next_page = response.urljoin(next_page)
        #     yield scrapy.Request(next_page, callback=self.parse)

    def parse_advert(self, response):
        def extract_with_css(query):
            return response.css(query).extract_first()

        yield self.parse_to_item(response)

    def parse_to_item(self, response):
        def get_float(text):
            # Function for reading float value from web page (should include decimal dot)
            result = re.findall(r'\d+\.*\d*', text)

            if len(result) > 0:
                return result[0]
            else:
                return 0

        def get_int(text):
            # Function for reading int value from web page even if it has separated thousands
            result = re.findall(r'\d+\ *\d*', text)

            if len(result) > 0:
                return result[0]
            else:
                return 0

        def get_m2(text):
            # Function for reading m2 value from web page, separated by free space
            results = re.findall(r'\d+', text)

            area = ''

            for result in results:
                # Get separate integers and connect them again together, it avoids empty spaces
                # and zeroes in wrong place
                area += str(int(result))

            if len(result) > 0:
                return area
            else:
                return 0

        def get_id(text):
            # Get advert id from string, it is always just integer number
            result = re.findall(r'\d+', text)

            if len(result) > 0:
                return result[0]
            else:
                return 0

        l = ItemLoader(item=Advert(), response=response)

        # Read ID from web page and sed it to function to get proper formating
        str_value = str(response.xpath('//div[@id="breadcrumbs"]/text()').extract())
        value = get_id(str_value)
        l.add_value('Id', value)

        # Find link on web page and save it to item
        l.add_xpath('Link', '//meta[@property="og:url"]/@content')

        # Read price from web page and get number in correct format
        str_value = str(response.xpath('//strong[@id="data-price"]/text()').extract())
        value = get_int(str_value)
        l.add_value('Price', value)

        # Get number of rooms item from parameters, not yet processed, for future
        l.add_xpath('NumberOfRooms', '//strong[@id="categoryNameJS"]/text()')   # categoryNameJS

        # Get all parameters of estate
        parameters = response.xpath('//div[@id="params"]/p')

        for parameter in parameters:
            # Get value of span parameter and based on that parse value to correct place
            text_tlste = str(parameter.xpath('.//span[@class="tlste"]/text()').extract())
            if "Úžitková plocha" in text_tlste:
                # Area in square meters
                str_area = str(parameter.xpath('.//strong/text()').extract())
                value = get_m2(str_area)
                l.add_value('LivingAreaM2', value)
            elif "Dátum aktualizácie" in text_tlste:
                # Last update of advert, [2,-2] is there to remove brackets and comas
                str_date = str(parameter.xpath('.//strong/text()').extract())[2:-2]
                l.add_value('LastUpdate', str_date)
            elif "Stav" in text_tlste:
                # Categorical new or older building, [2,-2] is there to remove brackets and comas
                str_age = str(parameter.xpath('.//strong/text()').extract())[2:-2]
                l.add_value('Age', str_age)
            elif "Plocha pozemku" in text_tlste:
                # Whole are in square meters
                str_area = str(parameter.xpath('.//strong/text()').extract())
                value = get_m2(str_area)
                l.add_value('LandAreaM2', value)
            elif "Lokalita" in text_tlste:
                # Location of estate
                str_location = parameter.xpath('.//strong/text()').extract()
                value = ''.join(str_location)
                l.add_value('Location', value)

        return l.load_item()

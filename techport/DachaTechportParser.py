import csv
import os
import grequests
import requests
from bs4 import BeautifulSoup


class SoloCategoryParse:
    def __init__(self, url_to_category):
        self.__url_to_category = url_to_category
        self.__main_page_url = 'https://www.techport.ru'
        self.__package_name = ''
        self.__attributes_id = dict()
        self.__attribute_number = 1
        self.__iteration = 0

    def parse(self):
        print('Start parsing!')
        resp = requests.get(f'{self.__main_page_url}{self.__url_to_category}')
        src = BeautifulSoup(resp.text, 'lxml')
        tcp_row = src.find('div', class_='tcp-row')
        print(tcp_row)
        tcp_containers = tcp_row.find_all('div', class_='tcp-directory-item')
        print(tcp_containers)
        for tcp_container in tcp_containers:
            self.__package_name = tcp_container.find('img').get('alt')
            category_url = tcp_container.find('a')
            url_subcategory = tcp_container.find('div', class_='tcp-directory-item__content').find_all('a',
                                                                                                       class_='tcp-directory-item__link two-lines')

            if len(url_subcategory) == 0:
                urls = self.parse_products_urls(category_url.get('href'))
                category = category_url.get('href')
                print(category)
                pages, pages_with_tables = self.get_product_pages(urls)
                self.parsing_products(pages, pages_with_tables, category_url.get('href'), category)
            else:
                for elem in url_subcategory:
                    urls = self.parse_products_urls(elem.get('href'))
                    category = elem.get('href')
                    print(category)
                    pages, pages_with_tables = self.get_product_pages(urls)
                    self.parsing_products(pages, pages_with_tables, elem.text, category)

    def get_product_pages(self, urls):
        print('Parsing product pages!')
        rs = (grequests.get(f'{self.__main_page_url}{u}') for u in urls)
        resp = grequests.map(rs, size=15)
        rs_with_table = (grequests.get(f'{self.__main_page_url}{url}/props') for url in urls)
        resp_with_table = grequests.map(rs_with_table, size=16)
        return resp, resp_with_table

    def parsing_products(self, pages, pages_with_tables, sub_package, category):
        sub_category_products_data = []
        sub_category_headers = []
        self.__attributes_id = dict()
        self.__attribute_number = 0
        for (product_page, product_page_with_table) in zip(pages, pages_with_tables):
            try:
                product_data = self.parseProduct(product_page.text, product_page_with_table.text, category)
            except AttributeError:
                continue
            for elem in product_data.keys():
                if not sub_category_headers.__contains__(elem):
                    sub_category_headers.append(elem)
            sub_category_products_data.append(product_data)
        print(self.__package_name)
        print(sub_package)
        if not os.path.exists(f'{self.__package_name}/{sub_package}'):
            os.makedirs(f'{self.__package_name}/{sub_package}')
        csv_name = sub_package.split("/")
        with open(f'{self.__package_name}/{sub_package}/{csv_name[len(csv_name) - 1]}.csv', 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=sub_category_headers, restval=None)
            writer.writeheader()
            for row in sub_category_products_data:
                writer.writerow(row)

    def parseProduct(self, page, page_with_table, category):
        print(f'Iteration#{self.__iteration}')
        data = dict()
        src = BeautifulSoup(page, 'lxml')
        images = src.find_all('img', class_='product_image')
        price = src.find('div', class_='tcp-col tcp-col_md-4 tcp-col_lg-3 tcp-right-block')
        new_price = price.find('div', class_='tcp-product-body__price')
        old_price = price.find('div', class_='tcp-product-body__old-price')
        img_str = ''
        name = src.find('h1', class_='tcp-dashboard-header__h1').text
        data['Name'] = name
        cat = category.split('/')[3:]
        if len(cat) > 1:
            cat_str = ''
            for el in cat:
                cat_str += f'{el} > '
            data['Categories'] = cat_str[:-3]
        else:
            data['Categories'] = category.split('/')[2:][0]

        for img in images:
            img_str += f"http://{img.get('src')[2:]}" + ','
        data['Images'] = img_str[:-1]
        if new_price is None:
            self.__iteration += 1
            return dict()
            # data['Regular price'] = None
            # data['Sale price'] = None
            # data['In stock?'] = 0
        elif old_price is None:
            new_price = new_price.text.strip().replace(' ', '')[:-4]
            data['Regular price'] = new_price
            data['Sale price'] = None
            data['In stock?'] = 1

        else:
            new_price = new_price.text.strip().replace(' ', '')[:-4]
            old_price = old_price.text.strip().replace(' ', '')[:-4]
            data['Regular price'] = old_price
            data['Sale price'] = new_price
            data['In stock?'] = 1
        props_soup = BeautifulSoup(page_with_table, 'lxml')
        table = props_soup.find('table', class_='tcp-specification tcp-specification_full tcp-specification_xs')
        trs = table.find_all('tr')
        for elem in trs:
            characteristic_name = f"{elem.find('td', class_='specification__name').text}"
            characteristic_value = elem.find('div', class_='tcp-specification__content').text
            if self.__attributes_id.get(characteristic_name) is None:
                self.__attributes_id[characteristic_name] = self.__attribute_number
                self.__attribute_number += 1
            if characteristic_name == 'Артикул':
                data['SKU'] = characteristic_value
            else:
                data[f'Attribute {self.__attributes_id.get(characteristic_name)} name'] = characteristic_name
                data[f'Attribute {self.__attributes_id.get(characteristic_name)} value(s)'] = characteristic_value
                data[f'Attribute {self.__attributes_id.get(characteristic_name)} visible'] = 1
                data[f'Attribute {self.__attributes_id.get(characteristic_name)} global'] = 1
        self.__iteration += 1
        return data

    def parse_products_urls(self, url):
        print(f'{self.__main_page_url}{url}')
        resp = requests.get(f'{self.__main_page_url}{url}')
        src = BeautifulSoup(resp.text, 'lxml')
        productUrls = []
        productsCount = int(src.find('span', class_='tcp-dashboard-header__count').text.split(' ')[0])
        offset = 0
        productsData = dict()
        productsData['SubCategory'] = url
        while offset < productsCount:
            page_url = f'{self.__main_page_url}{url}?offset={offset}'
            page = requests.get(page_url)

            page_soup = BeautifulSoup(page.text, 'lxml')
            catalogList = []
            try:
                catalogList = page_soup.find('div', {'id': 'catalog_list'}).find_all('a', class_='tcp-product__link')
            except AttributeError:
                print(page_url)
                exit(0)
            for product_link in catalogList:
                productUrls.append(product_link.get('href'))

            offset += 28
        return productUrls


if __name__ == '__main__':
    vstraivaemaya_byt_technika = SoloCategoryParse('/katalog/products/elektrotransport')
    vstraivaemaya_byt_technika.parse()
    print('done')

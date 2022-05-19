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
        self.__iteration = 0

    def parse(self):
        resp = requests.get(f'{self.__main_page_url}{self.__url_to_category}')
        src = BeautifulSoup(resp.text, 'lxml')
        tcp_row = src.find('div', class_='tcp-row')
        tcp_containers = tcp_row.find_all('div', class_='tcp-container')
        for tcp_container in tcp_containers:
            self.__package_name = tcp_container.find('div', class_='categories-block-button_title two-lines').text
            category_url = tcp_container.find('a')
            url_subcategory = tcp_container.find('div', class_='categories-block-cat tcp-js-scrollable').find_all('a',
                                                                                                                  class_='tcp-directory-item__link')
            print(category_url.get('href'))
            print(type(category_url.get('href')))
            print(url_subcategory)
            print(type(url_subcategory))
            if len(url_subcategory) == 0:
                urls = self.parse_products_urls(category_url.get('href'))
                pages, pages_with_tables = self.get_product_pages(urls)
                self.parsing_products(pages, pages_with_tables, category_url.get('href'))
            else:
                for elem in url_subcategory:
                    urls = self.parse_products_urls(elem.get('href'))
                    pages, pages_with_tables = self.get_product_pages(urls)
                    self.parsing_products(pages, pages_with_tables, elem.text)

    def get_product_pages(self, urls):
        print(urls)
        sites = [f'{self.__main_page_url}{u}' for u in urls]
        print(sites)
        rs = (grequests.get(f'{self.__main_page_url}{u}') for u in urls)
        resp = grequests.map(rs, size=16)
        rs_with_table = (grequests.get(f'{self.__main_page_url}{url}/props') for url in urls)
        resp_with_table = grequests.map(rs_with_table, size=16)
        print(resp)
        print(resp_with_table)
        return resp, resp_with_table

    def parsing_products(self, pages, pages_with_tables, sub_package):
        sub_category_products_data = []
        sub_category_headers = []
        for (product_page, product_page_with_table) in zip(pages, pages_with_tables):
            try:
                product_data = self.parseProduct(product_page.text, product_page_with_table.text)
            except AttributeError:
                continue
            for elem in product_data.keys():
                if not sub_category_headers.__contains__(elem):
                    sub_category_headers.append(elem)
            sub_category_products_data.append(product_data)
        print(f'{self.__package_name}/{sub_package}')
        if not os.path.exists(f'{self.__package_name}/{sub_package}'):
            os.makedirs(f'{self.__package_name}/{sub_package}')
        csv_name = sub_package.split("/")
        with open(f'{self.__package_name}/{sub_package}/{csv_name[len(csv_name) - 1]}.csv', 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=sub_category_headers, restval=None)
            writer.writeheader()
            for row in sub_category_products_data:
                writer.writerow(row)

    def parseProduct(self, page, page_with_table):
        print(f'Iteration#{self.__iteration}')
        data = dict()
        src = BeautifulSoup(page, 'lxml')
        images = src.find_all('img', class_='product_image')
        price = src.find('div', class_='tcp-product-body__new-price tcp-product-body-set__new-price')
        img_str = ''
        name = src.find('h1', class_='tcp-dashboard-header__h1').text
        data['Name'] = name
        for img in images:
            img_str += img.get('src')[2:] + '|'
        data['Images'] = img_str[:-1]
        if price is None:
            price = 0
        else:
            price = price.text.strip().replace(' ', '')[:-4]
        data['Price'] = price

        props_soup = BeautifulSoup(page_with_table, 'lxml')
        table = props_soup.find('table', class_='tcp-specification tcp-specification_full tcp-specification_xs')
        trs = table.find_all('tr')
        count = 0
        for elem in trs:
            data[f"{elem.find('td', class_='specification__name').text}"] = elem.find('div',
                                                                                      class_='tcp-specification__content').text
            count += 1
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
            catalogList = page_soup.find('div', {'id': 'catalog_list'}).find_all('a', class_='tcp-product__link')
            for product_link in catalogList:
                productUrls.append(product_link.get('href'))

            offset += 28
        return productUrls


if __name__ == '__main__':
    otduh_i_turizm = SoloCategoryParse('/katalog/products/otdyh-i-turizm')
    otduh_i_turizm.parse()
    umnyy_dom = SoloCategoryParse('/katalog/umnyy-dom')
    umnyy_dom.parse()
    elektrotransport = SoloCategoryParse('/katalog/products/elektrotransport')
    elektrotransport.parse()
    vse_dlya_detey = SoloCategoryParse('/katalog/products/vse-dlja-detej')
    vse_dlya_detey.parse()

import csv
import multiprocessing
import os
import time
from multiprocessing import Queue
import pandas as pd
import requests
from bs4 import BeautifulSoup

from techport.Utils import Utils


class Process(multiprocessing.Process):
    def __init__(self, utils):
        super().__init__()
        self.__utils = utils
        self.__mainPageUrl = 'https://www.techport.ru'
        self.__subs = Queue()
        self.__iteration = 0

    def parseSubCategory(self):
        categoryUrl = self.__utils.subs.get()
        resp = requests.get(f'{self.__mainPageUrl}{categoryUrl}')
        src = BeautifulSoup(resp.text, 'lxml')
        subCategories = src.find('ul', 'tcp-list-group__list').find_all('a', class_='')
        for elem in subCategories:
            self.__subs.put(elem.get("href"))

    def run(self):
        print('process started')
        while self.__utils.subs.qsize() != 0:
            self.parseSubCategory()
            sub_cat_url = self.__subs.get()
            productUrls = self.parseProductUrls(sub_cat_url)
            sub_category_products_data = []
            sub_category_headers = []
            for product_url in productUrls:
                product_data = self.parseProduct(product_url)
                for elem in product_data.keys():
                    if not sub_category_headers.__contains__(elem):
                        sub_category_headers.append(elem)
                sub_category_products_data.append(product_data)
            sub_cat_arr = sub_cat_url.split('/')
            sub_cat_name = sub_cat_arr[len(sub_cat_arr) - 1]
            # Process Process-2:
            # Traceback (most recent call last):
            #   File "/usr/lib/python3.10/multiprocessing/process.py", line 315, in _bootstrap
            #     self.run()
            #   File "/home/rapiera/Desktop/pythonProjects/igor_parser/techport/Process.py", line 46, in run
            #     os.makedirs(f'data{sub_cat_url}')
            #   File "/usr/lib/python3.10/os.py", line 225, in makedirs
            #     mkdir(name, mode)
            # FileExistsError: [Errno 17] File exists: 'data/katalog/products/melkobytovaja-tehnika/tehnika-dlja-kuhni'
            if not os.path.exists(f'{sub_cat_url}'):
                os.makedirs(f'data{sub_cat_url}')
            with open(f'data{sub_cat_url}/{sub_cat_name}.csv', 'w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=sub_category_headers, restval=None)
                writer.writeheader()
                for row in sub_category_products_data:
                    writer.writerow(row)
        print(f'Process with name: {self.name} done!')

    def parseProductUrls(self, url):
        resp = requests.get(f'{self.__mainPageUrl}{url}')
        src = BeautifulSoup(resp.text, 'lxml')
        productUrls = []
        productsCount = int(src.find('span', class_='tcp-dashboard-header__count').text.split(' ')[0])
        offset = 0
        productsData = dict()
        productsData['SubCategory'] = url
        while offset < productsCount:
            page_url = f'{self.__mainPageUrl}{url}?offset={offset}'
            page = requests.get(page_url)
            page_soup = BeautifulSoup(page.text, 'lxml')
            catalogList = page_soup.find('div', {'id': 'catalog_list'}).find_all('a', class_='tcp-product__link')
            for product_link in catalogList:
                productUrls.append(product_link.get('href'))

            offset += 28
        return productUrls

    def parseProduct(self, url):
        print(f'Iteration of process {self.name} #{self.__iteration}')
        resp = requests.get(f'{self.__mainPageUrl}{url}')
        data = dict()
        src = BeautifulSoup(resp.text, 'lxml')
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
        props = requests.get(f'{self.__mainPageUrl}{url}/props')
        props_soup = BeautifulSoup(props.text, 'lxml')
        table = props_soup.find('table', class_='tcp-specification tcp-specification_full tcp-specification_xs')

        # Traceback (most recent call last):
        #   File "/usr/lib/python3.10/multiprocessing/process.py", line 315, in _bootstrap
        #     self.run()
        #   File "/home/rapiera/Desktop/pythonProjects/igor_parser/techport/Process.py", line 38, in run
        #     product_data = self.parseProduct(product_url)
        #   File "/home/rapiera/Desktop/pythonProjects/igor_parser/techport/Process.py", line 94, in parseProduct
        #     trs = table.find_all('tr')
        # AttributeError: 'NoneType' object has no attribute 'find_all'
        trs = table.find_all('tr')
        count = 0
        for elem in trs:
            data[f"{elem.find('td', class_='specification__name').text}"] = elem.find('div',
                                                                                      class_='tcp-specification__content').text
            count += 1
        self.__iteration += 1
        return data


if __name__ == '__main__':
    utils = Utils()
    start_time = time.time()
    processes = []
    for _ in range(3):
        prc = Process(utils)
        processes.append(prc)
        prc.start()
    for elem in processes:
        elem.join()
    print("--- %s seconds ---" % (time.time() - start_time))

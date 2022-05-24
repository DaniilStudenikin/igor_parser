import csv
import os.path

import grequests
import requests
from bs4 import BeautifulSoup


class KillPrice24Parser:
    def __init__(self):
        self.__main_page_url = 'https://killprice24.ru/'
        self.__iteration = 0

    def parse_categories(self):
        response = requests.get(self.__main_page_url)
        categories = dict()
        src = BeautifulSoup(response.text, 'lxml')
        categories_urls = src.find('ul', {'id': 'nav'}).find_all('li', class_='level_1')
        for elem in categories_urls:
            categories[elem.find('a').text.strip()] = elem.find('a').get('href')
        return categories

    def get_all_product_urls(self, category_url):
        url = self.__main_page_url + category_url + '?page=all'
        response = requests.get(url)
        clean_urls = []
        src = BeautifulSoup(response.text, 'lxml')
        try:
            divs = src.find('ul', class_='row list-inline itemsList').find_all('div', class_='image')
            for div in divs:
                clean_urls.append(self.__main_page_url + div.find('a').get('href'))
            return clean_urls
        except AttributeError:
            return None

    def parse(self):
        categories_dict = self.parse_categories()
        for key, value in categories_dict.items():
            urls = self.get_all_product_urls(value)

            if urls is not None:
                data_to_csv = []
                headers_to_csv = []
                response = (grequests.get(url) for url in urls)
                resp = grequests.map(response, size=16)
                print(f'Parsing {key}!')
                for elem in resp:
                    try:
                        parsed_data = self.parse_product(elem.text)
                        data_to_csv.append(parsed_data)
                        for k in parsed_data.keys():
                            if not headers_to_csv.__contains__(k):
                                headers_to_csv.append(k)
                    except AttributeError:
                        print(elem.url)
                self.write_to_csv(headers_to_csv, data_to_csv, value, key)
            else:
                continue

    def write_to_csv(self, headers, data, package_path, csv_file_name):
        if csv_file_name.__contains__('/'):
            filename = csv_file_name.split('/')
            csv_file_name = ''
            for elem in filename:
                csv_file_name += elem + '_'
            csv_file_name = csv_file_name[:-1]
        if not os.path.exists(f'killprice24_old/data/{csv_file_name}'):
            os.makedirs(f'killprice24_old/data/{csv_file_name}')

        with open(f'killprice24_old/data/{csv_file_name}/{csv_file_name}.csv', 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers, restval=None)
            writer.writeheader()
            for row in data:
                writer.writerow(row)

    def parse_product(self, page_src):
        print(f'Iteration#{self.__iteration}')
        self.__iteration += 1
        data = dict()
        src = BeautifulSoup(page_src, 'lxml')
        product_name = src.find('div', class_='heading').text
        data['Name'] = product_name.strip()
        div_price = src.find('div', class_='price')
        try:
            old_price = div_price.find('strike').text.strip()
            data['Old price'] = old_price.replace(u'\xa0', '')
        except AttributeError:
            data['Old price'] = 0
        try:
            sale_price = div_price.find('span').text.strip()
            data['Sale price'] = sale_price.replace(u'\xa0', '')
        except AttributeError:
            data['Sale price'] = 0
        images_ = src.find('div', class_='image').find_all('a', class_='zoom')
        image_str = ''
        for img in images_:
            image_str += img.get('href') + '|'
        data['Images'] = image_str[:-1]
        # Характеристики есть не у всех
        info = src.find('div', {'id': 'profile'})
        if info is None:
            return data
        else:
            divs_data = info.find_all('div', class_='col-md-7 featuresList')
            for elem in divs_data:
                characteristic = elem.text.strip().split('\n')
                data[characteristic[0].strip()] = characteristic[1].strip()
            return data


def main():
    parser = KillPrice24Parser()
    parser.parse()


if __name__ == '__main__':
    main()

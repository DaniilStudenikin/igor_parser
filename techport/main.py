import csv
import os.path

from bs4 import BeautifulSoup
import requests


class TechportParser:
    def __init__(self):
        self.__mainPageUrl = 'https://www.techport.ru'
        self.__iteration = 0

    def parseCategories(self):
        resp = requests.get("https://www.techport.ru/katalog/products")
        src = BeautifulSoup(resp.text, 'lxml')
        categoriesUrls = src.find_all("a", class_='tcp-directory-item__heading')
        hrefs = []
        for elem in categoriesUrls:
            resp = requests.get(f'{self.__mainPageUrl}{elem.get("href")}')
            src = BeautifulSoup(resp.text, 'lxml')
            src = src.find('div', 'tcp-row')
            tcpContainers = src.find_all('div', class_="tcp-container")
            for elem in tcpContainers:
                a = elem.find('a')
                hrefs.append(a.get('href'))
        return hrefs

    def parseSubCategory(self):
        subs = []
        for elem in self.parseCategories():
            resp = requests.get(f'{self.__mainPageUrl}{elem}')
            src = BeautifulSoup(resp.text, 'lxml')
            subCategories = src.find('ul', 'tcp-list-group__list').find_all('a', class_='')
            for elem in subCategories:
                subs.append(elem.get("href"))
        return subs

    def Parse(self):
        subs = self.parseSubCategory()
        count = 0
        print('Start parsing!')
        for elem in subs:
            headers = 0
            resp = requests.get(f'{self.__mainPageUrl}{elem}')
            src = BeautifulSoup(resp.text, 'lxml')
            productsCount = int(src.find('span', class_='tcp-dashboard-header__count').text.split(' ')[0])
            count += productsCount
            offset = 0
            productsData = dict()
            productsData['SubCategory'] = elem
            if not os.path.exists(f'data/{elem}'):
                os.makedirs(f'data/{elem}')
            subCatName = elem.split('/')[-1]
            filename = f'data/{elem}/{subCatName}.csv'
            csv_file = open(filename, 'w', newline='')
            while offset < productsCount:
                url = f'{self.__mainPageUrl}{elem}?offset={offset}'
                page = requests.get(url)
                page_soup = BeautifulSoup(page.text, 'lxml')
                catalogList = page_soup.find('div', {'id': 'catalog_list'}).find_all('a', class_='tcp-product__link')
                for product_link in catalogList:
                    print(f'Iteration#{self.__iteration}')
                    data = self.parseProduct(product_link.get('href'))
                    for k, v in data.items():
                        productsData[k] = v

                    writer = csv.DictWriter(csv_file, fieldnames=productsData)
                    if headers == 0:
                        writer.writeheader()
                        headers += 1
                    writer.writerow(productsData)
                    self.__iteration += 1
                offset += 28

    def parseProduct(self, url):
        resp = requests.get(f'{self.__mainPageUrl}{url}')
        print(f'parsing product {self.__mainPageUrl}{url}')
        data = dict()
        src = BeautifulSoup(resp.text, 'lxml')
        images = src.find_all('img', class_='product_image')
        price = src.find('div', class_='tcp-product-body__new-price tcp-product-body-set__new-price')
        img_str = ''
        for img in images:
            img_str += img.get('src')[2:] + '|'
        data['Images'] = img_str[:-1]
        if price is None:
            price = 0
        else:
            price = price.text
        data['Price'] = price
        print(f'{self.__mainPageUrl}{url}/props parsing product table')
        props = requests.get(f'{self.__mainPageUrl}{url}/props')
        props_soup = BeautifulSoup(props.text, 'lxml')
        table = props_soup.find('table', class_='tcp-specification tcp-specification_full tcp-specification_xs')
        trs = table.find_all('tr')
        count = 0
        for elem in trs:
            data[f"Attribute#{count}:{elem.find('td', class_='specification__name').text}"] = elem.find('div',
                                                                                                        class_='tcp-specification__content').text
            count += 1
        return data


if __name__ == '__main__':
    techportParser = TechportParser()
    techportParser.Parse()

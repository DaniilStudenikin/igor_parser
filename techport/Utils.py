from multiprocessing import Queue

import requests
from bs4 import BeautifulSoup


class Utils:
    def __init__(self):
        self.__subs = Queue()
        self.__mainPageUrl = 'https://www.techport.ru'
        self.parseCategories()

    @property
    def subs(self):
        return self.__subs

    def parseCategories(self):
        print('parsing categories')
        resp = requests.get("https://www.techport.ru/katalog/products")
        src = BeautifulSoup(resp.text, 'lxml')
        categoriesUrls = src.find_all("a", class_='tcp-directory-item__heading')
        count = 0
        for elem in categoriesUrls:
            resp = requests.get(f'{self.__mainPageUrl}{elem.get("href")}')
            src = BeautifulSoup(resp.text, 'lxml')
            src = src.find('div', 'tcp-row')
            tcpContainers = src.find_all('div', class_="tcp-container")
            print(tcpContainers)
            for elem in tcpContainers:
                a = elem.find('a')
                count+=1
                print(f"URL FROM UTILS: {a.get('href')}")
                self.__subs.put(a.get('href'))
        print(count)

# if __name__ == '__main__':
#     utils = Utils()
#     utils.parseCategories()

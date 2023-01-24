import json
import os
import shutil
import time
import urllib.request
from bs4 import BeautifulSoup
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager


def scrap_truckscout24(url):
    ads = []
    result = {}

    driver = webdriver.Firefox(
        service=FirefoxService(GeckoDriverManager().install()))

    try:
        driver.get(url)
        driver.find_element(By.ID, 'consent-mgmt-accept-all').click()

        while True:
            driver.find_element(By.CLASS_NAME, 'ls-arrow').click()
            time.sleep(5)

            soup = BeautifulSoup(driver.page_source, 'lxml')
            truck_card = soup.find(
                class_='ls-top-cntnr'
            )

            truck_href = truck_card.find(
                class_='ls-titles'
            ).find('a').get('href')
            absolut_href = 'https://www.truckscout24.de' + truck_href

            truck_id = int(truck_href.split('/')[-2])

            title = ' - '.join(truck_card.find(
                class_='ls-title'
            ).text.replace('  ', ' ').strip().split('\n')[::-1])

            truck_description = truck_card.find(
                class_='short-description'
            ).text.replace('\xa0', '')

            truck_mileage = truck_card.find(
                class_='ls-data-additional'
            ).find('div').text
            if 'km' in truck_mileage:
                truck_mileage = int(
                    truck_mileage.replace('.', '').replace('km', '')
                )
            else:
                truck_mileage = 0

            color_and_power = truck_card.find(
                class_='columns'
            ).text
            if 'Farbe' in color_and_power:
                truck_color = color_and_power.split(
                    'Farbe'
                )[1].split('\n')[1].strip()
            else:
                truck_color = ''
            if 'Leistung' in color_and_power:
                truck_power = int(color_and_power.split(
                    'Leistung'
                )[1].split('kW')[0].strip())
            else:
                truck_power = 0

            dirty_price = truck_card.find(
                class_='ls-data-price'
            ).find('span').text.split(',')[0]
            truck_price = int(''.join([i for i in dirty_price if i.isdigit()]))

            truck = {
                'id': truck_id,
                'href': absolut_href,
                'title': title,
                'price': truck_price,
                'mileage': truck_mileage,
                'color': truck_color,
                'power': truck_power,
                'description': truck_description
            }

            i = 1
            for _ in truck_card.find_all(class_='gallery-picture__image')[:3]:
                img_name = f'{truck_id}_{i}.png'
                url = _.find("picture").find("img").get("data-src")
                if not Path(f'data/{truck_id}').exists():
                    os.makedirs(f'data/{truck_id}')
                urllib.request.urlretrieve(url, f"data/{truck_id}/{img_name}")
                i += 1

            ads.append(truck)

            element = driver.find_element(By.CLASS_NAME, 'next-page')
            if element.find_elements(By.CLASS_NAME, 'disabled'):
                break
            element.click()
            time.sleep(5)

        result['ads'] = ads
        with open('data/data.json', 'w', encoding="utf-8") as file:
            json.dump(result, file, indent=4, ensure_ascii=False)

    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()


def main():
    if Path('data').exists():
        shutil.rmtree('data', ignore_errors=True)

    url = 'https://www.truckscout24.de/transporter/gebraucht/kuehl-iso-frischdienst/renault'
    scrap_truckscout24(url)


if __name__ == '__main__':
    main()

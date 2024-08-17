#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import time
import requests
import io
import hashlib
import os
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager


# In[ ]:


def fetch_image_urls_util(url, driver_path):
    images = []
    options = Options()
    options.headless = True

    with webdriver.Chrome(service=Service(driver_path), options=options) as wd:
        try:
            wd.get(url)
        except Exception as e:
            print(f"ERROR - Could not open {url} - {e}")
            return []

        thumbnail_results = wd.find_elements(By.CSS_SELECTOR, "img.irc_mi")

        for img in thumbnail_results:
            src = img.get_attribute('src')
            if src and 'http' in src:
                images.append(src)

    return images


# In[ ]:


def fetch_image_urls(query, max_links_to_fetch, wd, sleep_between_interactions=1, driver_path=None, target_path=None, search_term=None):
    target_folder = os.path.join(target_path, '_'.join(search_term.lower().split(' ')))

    def scroll_to_end(wd):
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)

    search_url = f"https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={query}&oq={query}&gs_l=img"
    wd.get(search_url)

    image_urls = set()
    d = {}
    image_count = 0

    while image_count < max_links_to_fetch:
        scroll_to_end(wd)

        thumbnail_results = wd.find_elements(By.CSS_SELECTOR, "img.Q4LuWd")
        number_results = len(thumbnail_results)
        print(f"Found: {number_results} search results. Extracting links...")

        for img in thumbnail_results:
            try:
                img.click()
                time.sleep(sleep_between_interactions)
            except Exception as e:
                print(f"ERROR - Could not click image thumbnail - {e}")
                continue

            links = wd.find_elements(By.CSS_SELECTOR, "a[jsname='sTFXNd']")

            for link in links:
                href = link.get_attribute('href')
                if href and 'http' in href:
                    if href not in d:
                        d[href] = True
                        fetched_images = fetch_image_urls_util(href, driver_path)
                        for image_url in fetched_images:
                            if image_url and image_url not in image_urls:
                                image_urls.add(image_url)
                                image_count += 1

            if image_count >= max_links_to_fetch / 10:
                print(f"Saving {len(image_urls)} image links...")
                save_images(target_folder, image_urls)
                image_urls.clear()
                d.clear()

        if len(image_urls) >= max_links_to_fetch:
            print(f"Found: {len(image_urls)} image links, done!")
            break

    return image_urls


# In[ ]:



def save_images(folder_path, urls):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    for url in urls:
        persist_image(folder_path, url)


# In[ ]:


def persist_image(folder_path, url):
    try:
        image_content = requests.get(url).content
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file).convert('RGB')
        file_path = os.path.join(folder_path, hashlib.sha1(image_content).hexdigest()[:10] + '.jpg')
        with open(file_path, 'wb') as f:
            image.save(f, "JPEG", quality=85)
        print(f"SUCCESS - saved {url} as {file_path}")
    except Exception as e:
        print(f"ERROR - Could not download or save {url} - {e}")


# In[ ]:


def search_and_download(search_term, driver_path, target_path='./datasets', number_images=50):
    options = Options()
    options.headless = True

    target_folder = os.path.join(target_path, '_'.join(search_term.lower().split(' ')))
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    with webdriver.Chrome(service=Service(driver_path), options=options) as wd:
        fetch_image_urls(search_term, number_images, wd=wd, sleep_between_interactions=0.5, driver_path=driver_path, target_path=target_path, search_term=search_term)


# In[ ]:


if __name__ == '__main__':
    query = ["Serena Williams"]
    driver_path = ChromeDriverManager().install()

    for q in query:
        search_and_download(q, driver_path)


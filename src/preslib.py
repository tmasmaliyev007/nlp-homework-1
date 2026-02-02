# Built-In Functionalities
from .page import Page
from .utils import get_logger

# Requests & Parser
import requests
from bs4 import BeautifulSoup

# Utilities
import os
import time
from io import BytesIO

# Progress report
from tqdm import tqdm

# Image on OCR & Mathematical operations
import numpy as np
import cv2
import pytesseract as pyt

# Typing purposes
from typing import List

class PresLibScraper:
    def __init__(self) -> None:
        # Base topics
        self.topics: List[str] = [
            'informatics',
            'ecology'
            'history'
            'economy'
            'customs'
        ]

        # Base & Endpoint and Post urls
        self.base_url: str = 'https://www.preslib.az'
        self.endpoint: str = 'https://www.preslib.az/en/elibrary/ebooks/category/{}?page={}'
        self.post_url = 'https://www.preslib.az/en/elibrary/ebook/download/{}'

        # Logger
        self.logger = get_logger(self.__class__.__name__)

        # Session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5'
        })

        # Define directories
        os.makedirs('logs', exist_ok=True)
        os.makedirs('docs', exist_ok=True)
    
    def get_captcha_code(self, captcha_url: str) -> str:
        # Get Request
        response = self.session.get(captcha_url)
        response.raise_for_status()

        # Treat as bytes of open file
        img_bytes = BytesIO(response.content)

        # region Image Operations

        # Read image as OpenCV array
        img_arr = np.frombuffer(img_bytes.getvalue(), np.uint8)
        img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)

        # UpScale Image (2x)
        new_width = img.shape[1] * 2
        new_height = img.shape[0] * 2
        img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

        # Convert to grayscale
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        img = cv2.GaussianBlur(img, (3, 3), 0)

        # Apply median filter for denoising
        img = cv2.medianBlur(img, 3)

        # Remove gray lines, keep only white text
        _, cleaned_image = cv2.threshold(img, 220, 255, cv2.THRESH_BINARY)
        
        # Erosion followed by Dilation (removes small white noise)
        kernel = np.ones((2, 2), np.uint8)
        cleaned_image = cv2.morphologyEx(cleaned_image, cv2.MORPH_OPEN, kernel, iterations=1)

        # Centralize the text
        cleaned_image = cv2.copyMakeBorder(cleaned_image, 30, 30, 30, 0, borderType=cv2.BORDER_REPLICATE, value=[0, 0, 0])

        # endregion

        # OCR process
        config = r'--psm 7 --oem 3 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz0123456789'
        captcha_code: str = pyt.image_to_string(cleaned_image, config=config)

        # Format text
        captcha_code = captcha_code.replace('\n', '')

        return captcha_code
        

    def download_doc(self, url: str, destination: str) -> None:
        # Document ID
        doc_id = os.path.basename(url)

        # Get Request
        response = self.session.get(url)
        response.raise_for_status()

        # Parse HTML Content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get CSRF Token
        csrf_token = soup.find('input', {'name': 'csrf_preslib'}).get('value')

        # Get full url link of captcha image
        captcha_link = soup.find('img', {'class': 'rounded'}).get('src')
        f_captcha_url = '{}{}'.format(self.base_url, captcha_link)

        # Get captcha code from image
        captcha_code = self.get_captcha_code(f_captcha_url)

        # Define Post & Payload url
        p_url = self.post_url.format(doc_id)
        payload = {
            'csrf_preslib': csrf_token,
            'captcha': captcha_code
        }

        # Get stream output
        p_response = self.session.post(p_url, data=payload, stream=True)

        # Download document if status code is ok and doesn't send html header
        if p_response.status_code == 200 and p_response.headers.get('Content-Type', '') == 'application/octet-stream':
            f_path = '{}/{}.pdf'.format(destination, doc_id)

            with open(f_path, 'wb') as f:
                for chunk in p_response.iter_content(chunk_size=8192):
                    f.write(chunk)
                
            return True

        return False


    def scrape(self) -> None:
        for topic in self.topics:
            # Define pagination
            curr_page = Page(page=1)

            # Download count
            download_ctr = 0

            # Define output directory
            destination = f'docs/{topic}'
            os.makedirs(destination, exist_ok=True)

            self.logger.info(f"Processing Page {curr_page.page}")

            while not curr_page.is_last_page:
                try:
                    # Get Request
                    url = self.endpoint.format(topic, curr_page.page)
                    response = self.session.get(url)

                    # Check for error if there is any
                    response.raise_for_status()

                    # Parse HTML Content
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Find Article tags
                    article_tags = soup.find('div', {'class': 'row gx-md-3 gy-5 mb-3'})\
                                       .find_all('article')
                    
                    self.logger.info(f"Page {curr_page.page} - Extracted {len(article_tags)} documents.")
                    
                    for tag in tqdm(article_tags):
                        link = tag.find('a').get('href')

                        # Form full document url
                        f_doc_url = '{}{}'.format(self.base_url, link)

                        # Download document
                        status = self.download_doc(f_doc_url, destination)

                        # Get document id
                        doc_id = os.path.basename(url)

                        if status:
                            download_ctr+= 1
                            self.logger.info(f'Page {curr_page.page} - Topic {topic} - Downloaded document {doc_id}.')
                        else:
                            self.logger.info(f'Page {curr_page.page} - Topic {topic} - Error on book {doc_id}.')

                        self.logger.info(f'Page {curr_page.page} - Downloaded documents {download_ctr}/{len(article_tags)}')
                        time.sleep(5)

                    break

                except requests.HTTPError as e:
                    self.logger.error(f"Error on {topic} - Page - {curr_page}\n{e}")
                    break
            
            break
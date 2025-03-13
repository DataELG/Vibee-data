import requests
from bs4 import BeautifulSoup
import re
from unidecode import unidecode
from cleaning_functions import extraire_dates

def fetch_soup(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    result = requests.get(url, headers=headers)
    soup = BeautifulSoup(result.content , "html.parser")
    return soup

def fetch_event_id(soup_event) :
    event_id = soup_event.find('div', class_="tribe-events-back").find('div')['data-post-id']
    return event_id

def fetch_place(soup_event) :
    place_tag = soup_event.find('div', class_='tribe-events-schedule tribe-clearfix')
    place = place_tag.find('p').text.strip()
    return place

def fetch_date(soup_event) :
    date_tag = soup_event.find('div', class_='tribe-events-schedule tribe-clearfix')
    date = date_tag.find('h2')  
    date_text = ' '.join(unidecode(date).stripped_strings).upper().strip()
    
    return date_text

def fetch_coordinate(soup_event):
    gps = []
    event_info_flex = soup_event.find('div', class_= 'event-info-flex')
    event_info = event_info_flex.find_all('a')
    gps_tag = event_info[1]['href']
    match = re.search(r'([-+]?\d+\.\d+)%2C([-+]?\d+\.\d+)', gps_tag)
    if match:
        latitude = float(match.group(1))
        longitude = float(match.group(2))
        gps.append(longitude)
        gps.append(latitude)
    
    return gps

def fetch_event_tag(soup_event) :
    event_tag_list = []
    event_info_flex = soup_event.find('div', class_= 'event-info-flex')
    event_tags = event_info_flex.find('div', class_= 'event-tags').find_all('span')
    for event_tag in event_tags :
        event_tag_txt = unidecode(event_tag.text).upper().strip()
        if not event_tag_txt.startswith('FIN LE') and (not'GRATUIT' in event_tag_txt) and (not 'PAYANT' in event_tag_txt) and (not 'PRIX LIBRE' in event_tag_txt):
            event_tag_list.append(event_tag_txt)            

    return event_tag_list

def fetch_price(soup_event) :
    event_info_flex = soup_event.find('div', class_= 'event-info-flex')
    event_tags = event_info_flex.find('div', class_= 'event-tags').find_all('span')
    for event_tag in event_tags :
        event_tag_txt = unidecode(event_tag.text).upper().strip()
        if 'GRATUIT' in event_tag_txt or 'PAYANT' in event_tag_txt or 'PRIX LIBRE' in event_tag_txt:
            price = event_tag_txt
            return price
        
def fetch_description(soup_event, event_id) :
    event_content = soup_event.find('div', id = f'post-{event_id}')
    description = event_content.find('div', class_= 'tribe-events-single-event-description tribe-events-content').text.strip()
    return description

def fetch_image(soup_event, event_id) :
    event_content = soup_event.find('div', id = f'post-{event_id}')
    image = event_content.find('div', class_="tribe-events-event-image").find('img')['src']
    return image
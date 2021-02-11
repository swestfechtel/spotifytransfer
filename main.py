import csv
import signal
import ssl
import time
from multiprocessing import Pool, cpu_count, Value, Lock
from os import getpid, kill
import OpenSSL
import requests
from urllib3 import exceptions
import base64
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

client_id = '9c7dc5330ca142a691fd0959682d0761'
client_secret = '5ff88db8af1d4b1f97828479a33b5c1e'


def get_auth_token():
    tmp = client_id + ':' + client_secret
    tmp = tmp.encode('ascii')
    base64_code = base64.b64encode(tmp)
    base64_code = base64_code.decode('ascii')
    try:
        url = 'https://accounts.spotify.com/api/token'
        request = requests.post(url=url, headers={'Authorization': 'Basic ' + str(base64_code)}, data={'grant_type': 'client_credentials'})
    except OpenSSL.SSL.SysCallError as e:
        print(e)
        return None
    except ssl.SSLError as e:
        print(e)
        return None
    except exceptions.MaxRetryError as e:
        print(e)
        return None
    except requests.exceptions.SSLError as e:
        print(e)
        return None
    except:
        print("Unknown error. Unable to get further information.")
        return None

    data = request.json()
    return data['access_token'], data['expires_in']


def fetch_playlists(authorization):
    try:
        url = 'https://api.spotify.com/v1/users/gangstarappa/playlists'
        request = requests.get(url=url, headers={'Authorization': 'Bearer ' + authorization})
    except OpenSSL.SSL.SysCallError as e:
        print(e)
        return None
    except ssl.SSLError as e:
        print(e)
        return None
    except exceptions.MaxRetryError as e:
        print(e)
        return None
    except requests.exceptions.SSLError as e:
        print(e)
        return None
    except:
        print("Unknown error. Unable to get further information.")
        return None

    data = request.json()
    return data


def fetch_playlist(authorization, playlist_id):
    ret = list()
    try:
        offset = 0
        for i in range(10):
            url = 'https://api.spotify.com/v1/playlists/' + playlist_id + '/tracks'
            request = requests.get(url=url, headers={'Authorization': 'Bearer ' + authorization}, params={'offset': str(offset)})
            while request.status_code != 200:
                if request.status_code == 429:
                    retry = int(request.headers['Retry-After']) + 1
                    print(f"Process {getpid()}: Response code {request.status_code}. Retrying in {retry}s..")
                    time.sleep(retry)
                    request = requests.get(url=url, headers={'Authorization': 'Bearer ' + authorization}, params={'offset': str(offset)})
                elif request.status_code == 403:
                    print(f"Process {getpid()}: Response code {request.status_code}. Killing process.")
                    kill(getpid(), signal.SIGTERM)
                    return None
                else:
                    print(f"Response code {request.status_code}. Ending query chain.")
                    return None

            offset += 100
            data = request.json()
            # print(data)
            ret.append(data)
    except OpenSSL.SSL.SysCallError as e:
        print(e)
        return None
    except ssl.SSLError as e:
        print(e)
        return None
    except exceptions.MaxRetryError as e:
        print(e)
        return None
    except requests.exceptions.SSLError as e:
        print(e)
        return None
    except:
        print("Unknown error. Unable to get further information.")
        return None

    return ret


if __name__ == '__main__':
    access_token, expires_in = get_auth_token()
    playlists_raw = fetch_playlists(access_token)
    playlists = dict()
    for playlist in playlists_raw['items']:
        playlists[playlist['name']] = playlist['id']

    tracks_raw = fetch_playlist(access_token, playlists['#EDMParty'])
    # print(tracks_raw)
    # tracks_raw = playlist_raw['tracks']
    track_names = list()
    for item in tracks_raw:
        for track in item['items']:
            track_names.append(track['track']['name'])

    print(len(track_names))
    driver = webdriver.Chrome(r'E:/Program Files (x86)/Chromedriver/chromedriver.exe')
    driver.get('https://music.amazon.de/search')
    # driver.implicitly_wait(5)

    # sign_in_button = driver.find_element_by_id('signInButton')
    sign_in_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'signInButton'))
    )
    sign_in_button.click()

    # """
    email_input = driver.find_element_by_name('email')
    password_input = driver.find_element_by_name('password')
    submit_button = driver.find_element_by_id('signInSubmit')
    # """
    """
    email_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, 'email'))
    )
    password_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, 'password'))
    )
    submit_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, 'signInSubmit'))
    )
    """
    email_input.send_keys('simon.westfechtel@gmail.com')
    password_input.send_keys('ho9nktdoiPme5SspSQLd')
    submit_button.click()

    for song in track_names:
        """
        navbar_search_input = driver.find_element_by_id('navbarSearchInput')
        """
        # """
        navbar_search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'navbarSearchInput'))
        )
        # """
        navbar_search_input.send_keys(song)
        navbar_search_input.send_keys(Keys.RETURN)

        time.sleep(1)
        # """
        hydrated_elements = driver.find_elements_by_class_name('hydrated')
        # """
        """
        hydrated_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'hydrated'))
        )
        """

        play = hydrated_elements[17]
        play.click()

        context_menu = hydrated_elements[19]
        context_menu.click()

        # """
        add_to_playlist = driver.find_element_by_id('contextMenuOption1')
        # """
        """
        add_to_playlist = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'contextMenuOption1'))
        )
        """
        add_to_playlist.click()

        time.sleep(1)
        # """
        playlist = driver.find_element_by_class_name('col1')
        # """
        """
        playlist = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'col1'))
        )
        """
        playlist.click()

    driver.quit()

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
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from difflib import SequenceMatcher
from tqdm import tqdm
import pickle

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
    except Exception as e:
        print(e)
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
    except Exception as e:
        print(e)
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
    except Exception as e:
        print(e)
        return None

    return ret


def get_playlists(raw):
    playlists = dict()
    for playlist in raw['items']:
        playlists[playlist['name']] = playlist['id']

    return playlists


def get_track_names(raw):
    track_names = list()
    for item in raw:
        for track in item['items']:
            tmp = dict()
            tmp['name'] = track['track']['name']
            artists = [x['name'] for x in track['track']['artists']]
            tmp['artists'] = artists
            track_names.append(tmp)

    return track_names


def setup_driver(headless=False):
    options = ChromeOptions()
    # options = FirefoxOptions()
    options.add_argument('--no-proxy-server')
    options.add_argument("--proxy-server='direct://'")
    options.add_argument('--proxy-bypass-list=*')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--window-size=1920,1080')
    if headless:
        options.add_argument('--headless')
    driver = webdriver.Chrome(options=options, executable_path=r'E:/Program Files (x86)/Webdriver/chromedriver.exe')
    # driver = webdriver.Firefox(options=options, executable_path=r'E:/Program Files (x86)/Webdriver/geckodriver.exe')
    # driver.implicitly_wait(10)
    driver.get('https://music.amazon.de/search')
    return driver


def sign_in(driver):
    sign_in_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'signInButton'))
    )
    sign_in_button.click()

    email_input = driver.find_element_by_name('email')
    password_input = driver.find_element_by_name('password')
    submit_button = driver.find_element_by_id('signInSubmit')

    email_input.send_keys('simon.westfechtel@gmail.com')
    password_input.send_keys('ho9nktdoiPme5SspSQLd')
    submit_button.click()


def check_top_result(song, driver, music_container):
    # check if top search result matches and try to add
    # select wrapper for top results
    music_container_top = music_container.find_elements_by_tag_name('music-container')[0]

    # select wrapper for top song result
    music_horizontal_item_top = music_container_top.find_element_by_tag_name('music-horizontal-item')

    # find shadow root for wrapper
    shadow_root_top = driver.execute_script('return arguments[0].shadowRoot', music_horizontal_item_top)

    # find song and artist names
    div_center_top = shadow_root_top.find_element_by_class_name('center')
    song_name_top = div_center_top.find_element_by_tag_name('a')
    span_top = div_center_top.find_element_by_tag_name('span')
    artist_top = span_top.find_element_by_tag_name('a')

    # check if (song and) artist names match
    if (
            any(SequenceMatcher(a=x, b=artist_top.get_attribute('text')).ratio() > 0.75 for x in song['artists'])
            or
            any(x in artist_top.get_attribute('text') for x in song['artists'])
    ):

        # find div to hover
        div_top = shadow_root_top.find_element_by_tag_name('div')
        builder_top = ActionChains(driver)
        builder_top.move_to_element(div_top).perform()

        # find button for context menu
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.TAG_NAME, 'music-button'))
        )
        music_button_top = music_container_top.find_elements_by_tag_name('music-button')[1]
        shadow_root_top = driver.execute_script('return arguments[0].shadowRoot', music_button_top)
        button_top = shadow_root_top.find_element_by_tag_name('button')
        button_top.click()

        # find button to add to playlist
        add_to_playlist = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'contextMenuOption1'))
        )
        # add_to_playlist = driver.find_element_by_id('contextMenuOption1')
        add_to_playlist.click()

        playlist = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'col1'))
        )
        playlist.click()

        return True

    return False


def check_song_results(song, driver, music_container):
    # cycle songs for correct result
    # find wrapper for song results
    music_container = music_container.find_elements_by_tag_name('music-container')[1]

    # find wrappers for songs
    music_items = music_container.find_elements_by_tag_name('music-horizontal-item')

    # cycle through song results
    for music_item in music_items:

        # find artist name
        builder = ActionChains(driver)
        shadow_root = driver.execute_script('return arguments[0].shadowRoot', music_item)
        center_div = shadow_root.find_element_by_class_name('center')
        span = center_div.find_element_by_tag_name('span')
        music_link = span.find_element_by_tag_name('music-link')
        artist = music_link.find_element_by_tag_name('a')

        # check if artist name matches
        if (
                any(SequenceMatcher(a=x, b=artist.get_attribute('text')).ratio() > 0.75 for x in song['artists'])
                or
                any(x in artist.get_attribute('text') for x in song['artists'])
        ):

            div = shadow_root.find_element_by_tag_name('div')
            builder.move_to_element(div).perform()

            WebDriverWait(music_item, 10).until(
                EC.visibility_of_element_located((By.TAG_NAME, 'music-button'))
            )
            context_button = music_item.find_elements_by_tag_name('music-button')[1]
            shadow_root = driver.execute_script('return arguments[0].shadowRoot', context_button)
            button = shadow_root.find_element_by_tag_name('button')
            button.click()

            add_to_playlist = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, 'contextMenuOption1'))
            )
            # add_to_playlist = driver.find_element_by_id('contextMenuOption1')
            add_to_playlist.click()

            playlist = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'col1'))
            )
            playlist.click()

            return True
        else:
            continue

    return False


def transfer_songs(driver, track_names, second_search=False):
    failed_songs = []
    i = 0
    print(f"trying to add {len(track_names)} songs...")

    for song in tqdm(track_names):
        try:
            driver.get('https://music.amazon.de/search')

            i += 1
            if i % 25 == 0:
                print(f"elapsed {i} songs so far")

                # Wait for searchbar to appear
            navbar_search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'navbarSearchInput'))
            )

            # enter song name into searchbar
            navbar_search_input.send_keys(song['name'] if not second_search else song['name'] + ' ' + song['artists'][0])
            navbar_search_input.send_keys(Keys.RETURN)

            # find outer wrapper
            music_container = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.TAG_NAME, 'music-container'))
            )
            # music_container = driver.find_element_by_tag_name('music-container')

            # check top result
            try:
                if check_top_result(song, driver, music_container):
                    continue
            except Exception as e:
                pass
                # raise e

            try:
                if check_song_results(song, driver, music_container):
                    continue
            except Exception as e:
                raise e

            failed_songs.append(song)
            # print(f"failed to add song {song} due to bad search result")

        except Exception as e:
            # print(f"failed to add song {song} due to error")
            # print(e)
            # driver.get('https://music.amazon.de/search')
            failed_songs.append(song)
            continue

    print(f"added {len(track_names) - len(failed_songs)} songs (out of {len(track_names)})")
    return failed_songs


if __name__ == '__main__':
    access_token, expires_in = get_auth_token()
    playlists_raw = fetch_playlists(access_token)
    playlists = get_playlists(playlists_raw)
    tracks_raw = fetch_playlist(access_token, playlists['#EDMParty'])
    t_names = get_track_names(tracks_raw)
    # t_names = t_names[:50]
    d = setup_driver(False)
    sign_in(d)
    f_songs = transfer_songs(d, t_names)
    if len(f_songs) > 0:
        f_songs = transfer_songs(d, f_songs, True)

    with open('outfile', 'wb') as fp:
        pickle.dump(f_songs, fp)

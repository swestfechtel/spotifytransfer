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

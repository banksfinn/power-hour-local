from flask import Flask
from flask import redirect, request
import requests
from itsdangerous import base64_encode

app = Flask(__name__)

url = "http://172.23.69.67:3412"

access_token = "BQCYY6xhCWE42TcVpFFrHwkKRDURwkA0oGhPb3UA4sGr3ApswmypoIHDLLoQBfGyNbHAXKPAQkyRIK8b1G782q3LsP2bkDekNRRVN-ajsjsJUhVGalU64uB0hytgcp9S-1pzX5VJEhNXt5xKjFDzTIulXAiqL8EUU9kX4S-ZD9REOK9raGpw1dH-GqcnyivXI1H0EqjvQjegF0PvffY354KH"
refresh_token = "AQDYz4OvOWQBae3YB5spC5vg8WqQvYGYHasox2w_sVO9kWfw62beTFKy1UItJKn9pMiiWw5hvUlk4QqVSvv0w2XYgtTu6EBExInjtm9xf3t0pP89Vadsa_U8f-L8qfA624g"

@app.route("/spotify/login", methods=["GET"])
def spotifyLogin():
    return redirect(f"https://accounts.spotify.com/authorize?scope=user-read-private user-read-email user-read-playback-state user-modify-playback-state playlist-read-private&client_id=9bde2bdebbc740079240780a10d238c4&response_type=code&redirect_uri={url}/spotify/callback")


@app.route("/spotify/callback", methods=["GET"])
def spotifyCallback():
    code = request.args["code"]
    headers = {
        "Authorization": "Basic " + base64_encode("9bde2bdebbc740079240780a10d238c4:1d3064e898e64996a8582d29af80acf4").decode(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    r = requests.post(
        "https://accounts.spotify.com/api/token", data={
            "grant_type": "authorization_code",
            "redirect_uri": f"{url}/spotify/callback",
            "code": code
        }, headers=headers)
    

    access_token = r.json()["access_token"]
    refresh_token = r.json()["refresh_token"]
    
    print("Access Token")
    print(access_token)
    print("Refresh Token")
    print(refresh_token)

    return 200


@app.route("/spotify/playlists", methods=["GET"])
def get_playlists():
    # Get playlists from a user
    if request.method == "OPTIONS":
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type, Access-Control-Allow-Headers, Origin,Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers, Spotify-Access-Token, Spotify-Refresh-Token',
            'Access-Control-Max-Age': '3600',
        }
        return ('', 204, headers)

    r = requests.get("https://api.spotify.com/v1/me/playlists?limit=25",
                     headers={"Authorization": "Bearer " + access_token})
    if r.status_code == 401:
        r = requests.get("https://api.spotify.com/v1/me/playlists?limit=25",
                         headers={"Authorization": "Bearer " + access_token})
        return (r.json(), 200)

    return (r.json(), 200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3412)


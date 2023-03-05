from http.client import BAD_REQUEST
import json
from math import floor
import time
import uuid
from datetime import datetime
from itsdangerous import base64_encode
import requests
import random
from threading import Thread



access_token = "BQCYY6xhCWE42TcVpFFrHwkKRDURwkA0oGhPb3UA4sGr3ApswmypoIHDLLoQBfGyNbHAXKPAQkyRIK8b1G782q3LsP2bkDekNRRVN-ajsjsJUhVGalU64uB0hytgcp9S-1pzX5VJEhNXt5xKjFDzTIulXAiqL8EUU9kX4S-ZD9REOK9raGpw1dH-GqcnyivXI1H0EqjvQjegF0PvffY354KH"
refresh_token = "AQDYz4OvOWQBae3YB5spC5vg8WqQvYGYHasox2w_sVO9kWfw62beTFKy1UItJKn9pMiiWw5hvUlk4QqVSvv0w2XYgtTu6EBExInjtm9xf3t0pP89Vadsa_U8f-L8qfA624g"
playlist_id = "3WSeteAA0wpziNg4tyWcYy"


def refresh_token(refresh_token):
    # Utility function to refresh the token
    headers = {
        "Authorization": "Basic " + base64_encode("9bde2bdebbc740079240780a10d238c4:1d3064e898e64996a8582d29af80acf4").decode(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    r = requests.post(
        "https://accounts.spotify.com/api/token", data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }, headers=headers)
    return r.json()["access_token"]




class PowerHourRequest:
    def __init__(self,
                 playlist_id,
                 access_token,
                 refresh_token,
                 num_songs,
                 beer_sound,
                 time_per_song,
                 play_halfway_there,
                 play_final_countdown,
                 shuffle_playlist):
        self.playlist_id = playlist_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.num_songs = num_songs
        self.shuffle_playlist = shuffle_playlist
        self.beer_sound = beer_sound
        self.time_per_song = time_per_song
        self.play_halfway_there = play_halfway_there
        self.play_final_countdown = play_final_countdown
        self.active = False
        self.initiate = True
        self.id = uuid.uuid4()

    def generate_headers(self):
        return {"Authorization": "Bearer " + self.access_token}

    def make_request(self, url, request_function, data=None):
        response = request_function(
            url, headers=self.generate_headers(), data=data)
        if response.status_code == 401:
            print("Refreshing token...")
            self.access_token = refresh_token(self.refresh_token)
            print("Token has been refreshed")
            # Repeat the same thing again
            return self.make_request(url, request_function)
        elif response.status_code > 399:
            print(response)
            print(response.reason)
        else:
            return response

    def play_song(self, song_id, start_from_beginning=False):
        if self.beer_sound:
            self.make_request(
                url="https://api.spotify.com/v1/me/player/play",
                request_function=requests.put,
                data=json.dumps(
                    {"uris": ["spotify:track:1EHDQzi4iWbq6jmF6GqXNc"], "position_ms": 4000})
            )
            time.sleep(1)

        start_time = self.get_hype_part(song_id)
        if start_from_beginning:
            start_time = 0
        self.make_request(
            url="https://api.spotify.com/v1/me/player/play",
            request_function=requests.put,
            data=json.dumps(
                {"uris": ["spotify:track:" + song_id], "position_ms": start_time * 1000}),
        )

    def get_songs(self, playlist_id):
        r = self.make_request(
            url="https://api.spotify.com/v1/playlists/" + playlist_id,
            request_function=requests.get
        )
        return r.json()["tracks"]["items"]

    def check_conditional_songs(self, index):
        if index == self.num_songs // 2 - 1:
            # Livin' on a Prayer
            return "37ZJ0p5Jm13JPevGcx4SkF"
        elif index == self.num_songs - 1:
            # Final Countdown
            return "3MrRksHupTVEQ7YbA0FsZK"
        return ""

    def initiate_power_hour(self):
        print("Starting power hour!")
        songs = self.get_songs(self.playlist_id)

        # Shuffle songs
        if self.shuffle_playlist:
            random.shuffle(songs)

        self.active = True
        for i in range(self.num_songs):
            if not self.active:
                break

            conditional_song = self.check_conditional_songs(i)
            if conditional_song:
                self.play_song(conditional_song,
                               conditional_song == "3MrRksHupTVEQ7YbA0FsZK")
            else:
                print(
                    f"Playing song: {songs[i]['track']['name']} as song {i} of {self.num_songs}"
                )
                self.play_song(songs[i]["track"]["id"])

            time.sleep(self.time_per_song -
                       1 if self.beer_sound else self.time_per_song)

        self.end_power_hour()


    def get_hype_part(self, song_id):
        r = self.make_request(
            url="https://api.spotify.com/v1/audio-analysis/" + song_id,
            request_function=requests.get,
        )
        song_analysis = r.json()
        sections = song_analysis["segments"]
        max_loudness = -1000
        max_index = -1
        for i, section in enumerate(sections):
            if section["loudness_max"] > max_loudness:
                max_loudness = section["loudness_max"]
                max_index = i

        # this is the amount of time on either end of the loudest part
        # we want, to prevent cutting off immediately after the peak
        min_padding = floor(self.time_per_song / 3)
        time_before = sections[max_index]["duration"] * -1
        start_position = max_index
        while start_position > 0:
            time_before += sections[start_position]["duration"]
            if time_before > min_padding:
                break
            start_position -= 1

        # we do * -1 so we don't count the hype part
        time_after = sections[max_index]['duration'] * -1
        end_position = max_index
        while end_position < len(sections) - 1:
            time_after += sections[end_position]["duration"]
            if time_after > min_padding:
                break
            end_position += 1

        total_time = time_before + sections[max_index]["duration"] + time_after
        while total_time < self.time_per_song:
            if start_position > 0 and end_position < len(sections) - 1:
                # We have available segments on both sides
                # Case 1, start is louder
                if sections[start_position]["loudness_max"] > sections[end_position]["loudness_max"]:
                    total_time += sections[start_position]["duration"]
                    start_position -= 1
                else:
                    total_time += sections[end_position]["duration"]
                    end_position += 1

            elif start_position > 0:
                # Then we are at the end of the song
                total_time += sections[start_position]["duration"]
                start_position -= 1
            elif end_position < len(sections) - 1:
                total_time += sections[end_position]["duration"]
                end_position += 1
            else:
                return 0
        return sections[start_position]["start"]
    

def start_power_hour():
    power_hour_request = PowerHourRequest(playlist_id=playlist_id,
                                        access_token=access_token,
                                        refresh_token=refresh_token,
                                        num_songs=60,
                                        shuffle_playlist=True,
                                        beer_sound=True,
                                        time_per_song=60,
                                        play_final_countdown=True,
                                        play_halfway_there=True)
    power_hour_request.initiate_power_hour()


start_power_hour()
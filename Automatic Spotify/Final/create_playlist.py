import json
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
import youtube_dl

from secrets import spotify_user_id, spotify_token

class CreatePlaylist:
    def __init__(self):
        self.user_id = spotify_user_id
        self.spotify_token = spotify_token
        self.youtube_client = self.get_yt_client()
        self.all_song_info = {}
    # log into yt
    def get_yt_client(self):
        """ Log Into Youtube, Copied from Youtube Data API """
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    # grab liked videos
    def get_liked_vids(self):
        request = self.youtube_client.videos().list(
            part="snippet,conentDetails,statistics",
            myRating="like"
        )
        response = request.execute()

        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])

            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url,download=False)

            song_name = video["track"]
            artist = video["artist"]

            self.all_song_info[video_title]={
                "youtube_url":youtube_url,
                "song_name":song_name,
                "artist":artist,
                "spotify_uri":self.get_spotify_uri(song_name,artist)
            }


    # create a new playlist
    def create_palylist(self):
        request_body = json.dumps(
            {
                "name": "Youtube Liked VIDS",
                "description": "All Liked YouTube Videos",
                "public": True
            }
        )
        query ="https://api.spotify.com/v1/users/{}/playlist".fomat(self.user_id)
        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type":"application/json",
                "Authorization":"Bearer {}".format(spotify_token)
            }
        )
        response_json = response.json()
        return response_json("id")
    # search for the song
    def get_spotify_uri(self, song_name, artist):

        query =  "https://api.spotify.com/v1/search?q=track%3A{}+artist%3A{}&type=track&limit=20&offset=0".format(
            song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                "Content-Type: application/json",
                "Authorization: Bearer {}".format(self.spotify_token)
            }
        )
        response_json = response.json()
        songs = response_json["tracks"]["items"]

        # use only first song
        uri = songs[0]["uri"]

        return uri
    # add this song to playlist
    def add_song_to_playlist(self):
        # fill in song dict
        self.get_liked_vids()
        # collect uri
        uris = []
        for song, info in self.all_song_info.items():
            uris.append(info["spotify_uri"])
        # create a new playlist
        playlist_id = self.create_palylist()
        #add songs into playlist
        request_data = json.dumps(uris)

        query  = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response = requests.post(
            query,
            data = request_data,
            headers = {
                "Content-Type: application/json",
                "Authorization: Bearer {}".format(self.spotify_token)
            }
        )
        response_json = response.json()
        return response_json


if __name__ == '__main__':
    cp = CreatePlaylist()
    cp.add_song_to_playlist()
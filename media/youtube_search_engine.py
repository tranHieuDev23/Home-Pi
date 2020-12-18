import os
import random
from googleapiclient.discovery import build
import pafy
from dotenv import load_dotenv
load_dotenv()

# API Key for YouTube Search Engine
GOOGLE_CLOUD_API_KEY = os.getenv('GOOGLE_CLOUD_API_KEY')
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'


# Function to search YouTube and get video id
def youtube_search(query, maximum=1):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=GOOGLE_CLOUD_API_KEY)

    search_response = youtube.search().list(
        q=query,
        part='id,snippet'
    ).execute()

    videos = []
    channels = []
    playlists = []
    video_ids = []
    channel_ids = []
    playlist_ids = []

    # Add each result to the appropriate list, and then display the lists of
    # matching videos, channels, and playlists.

    for search_result in search_response.get('items', []):
        if search_result['id']['kind'] == 'youtube#video':
            videos.append('%s (%s)' % (search_result['snippet']['title'],
                                       search_result['id']['videoId']))
            video_ids.append(search_result['id']['videoId'])

        elif search_result['id']['kind'] == 'youtube#channel':
            channels.append('%s (%s)' % (search_result['snippet']['title'],
                                         search_result['id']['channelId']))
            channel_ids.append(search_result['id']['channelId'])

        elif search_result['id']['kind'] == 'youtube#playlist':
            playlists.append('%s (%s)' % (search_result['snippet']['title'],
                                          search_result['id']['playlistId']))
            playlist_ids.append(search_result['id']['playlistId'])

    # Checks if your query is for a channel, playlist or a video and changes the URL accordingly
    if ('channel' in str(query).lower() and len(channels) != 0):
        url_id = channel_ids[0]
        channel_response = youtube.channels().list(
            id=url_id,
            part='contentDetails'
        ).execute()
        url_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        list_response = youtube.playlistItems().list(
            playlistId=url_id,
            part='contentDetails'
        ).execute()
        if maximum == 1:
            list_result = random.choice(list_response.get('items', []))
            return list_result['contentDetails']['videoId']
        else:
            ids = []
            for list_result in list_response.get('items', []):
                ids.append(list_result['contentDetails']['videoId'])
                if len(ids) >= maximum:
                    return ids
            return ids
    elif('playlist' in str(query).lower() and len(playlists) != 0):
        url_id = playlist_ids[0]
        list_response = youtube.playlistItems().list(
            playlistId=url_id,
            part='contentDetails'
        ).execute()
        if maximum == 1:
            list_result = random.choice(list_response.get('items', []))
            return list_result['contentDetails']['videoId']
        else:
            ids = []
            for list_result in list_response.get('items', []):
                ids.append(list_result['contentDetails']['videoId'])
                if len(ids) >= maximum:
                    return ids
            return ids
    elif(len(video_ids) != 0):
        if maximum == 1:
            return video_ids[0]
        else:
            ids = []
            for id in video_ids:
                ids.append(id)
                if len(ids) >= maximum:
                    return ids
            return ids
    else:
        return [] if maximum > 1 else None


# Function to get streaming links for YouTube URLs
def youtube_stream_link(video_url):
    video = pafy.new(video_url)
    best_video = video.getbest()
    best_audio = video.getbestaudio()
    audio_streaming_link = best_audio.url
    video_streaming_link = best_video.url
    return audio_streaming_link, video_streaming_link

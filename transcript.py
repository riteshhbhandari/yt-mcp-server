"""
transcript.py

Handles extracting the video ID from a YouTube URL and fetching
the transcript for that video using youtube-transcript-api.
and translating the transcript to english using Gemini API if the transcript is not in English.
"""

import re
import yt_dlp

from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
from config import GEMINI_API_KEY, MODEL
from google import genai
from prompt import LANGUAGE_TRANSLATION_PROMPT


import database
client = genai.Client(api_key=GEMINI_API_KEY)

def extract_video_id(url: str) -> str:
    """
    Extract the YouTube video ID from a URL.

    Supports formats like:
      - https://www.youtube.com/watch?v=VIDEO_ID
      - https://youtu.be/VIDEO_ID
      - https://www.youtube.com/shorts/VIDEO_ID
      - https://www.youtube.com/embed/VIDEO_ID
    """
    if not url:
        raise ValueError("URL cannot be empty.")

    parsed = urlparse(url)

    # https://youtu.be/VIDEO_ID
    if parsed.hostname in ("youtu.be",):
        video_id = parsed.path.lstrip("/")
        if video_id:
            return video_id

    # https://www.youtube.com/watch?v=VIDEO_ID
    if parsed.hostname and "youtube.com" in parsed.hostname:
        if parsed.path == "/watch":
            query = parse_qs(parsed.query)
            video_id = query.get("v", [None])[0]
            if video_id:
                return video_id

        # /shorts/VIDEO_ID or /embed/VIDEO_ID
        match = re.match(r"^/(shorts|embed)/([a-zA-Z0-9_-]+)", parsed.path)
        if match:
            return match.group(2)

    # Fallback: try to find an 11-character video-id-like pattern anywhere in the URL
    fallback_match = re.search(r"([a-zA-Z0-9_-]{11})", url)
    if fallback_match:
        return fallback_match.group(1)

    raise ValueError(f"Could not extract video ID from URL: {url}")


def get_transcript(url: str) -> dict:
    """
    Given a YouTube URL, fetch and return the full transcript as a single string.
    """
    video_id = extract_video_id(url)
    video_meta_data = get_video_metadata(url)
    print("Video Metadata:", video_meta_data)

    if(database.get_video(video_id)==0):
        print("Video not found in database.")
        print("Transcribing using AI...")
        try:
            # transcript_language = Fetch the languages list the teanscript is available 
            # transcript = Fetch the first available language fro transcript_language
            transcript_language= YouTubeTranscriptApi().list(video_id)
            transcript = next(iter(transcript_language))

            print("transcript_language", transcript_language)
            print("language: " + transcript.language_code)

            if(transcript.language_code != "en" or "en-IN" ):
                transcript_list= YouTubeTranscriptApi().fetch(
                    video_id,
                    languages=[transcript.language_code])
                full_text = " ".join(snippet.text for snippet in transcript_list)
                #call translate_to_english function to translate the transcript to english
                full_text = translate_to_english(full_text, transcript_list.language_code)
            else :
                transcript_list = YouTubeTranscriptApi().fetch(video_id)
                full_text = " ".join(snippet.text for snippet in transcript_list)
            # print("Language:",transcript_list.language,"Language Code:", transcript_list.language_code)
    
        except TranscriptsDisabled:
            raise RuntimeError("Transcripts are disabled for this video.")
        except NoTranscriptFound:
            raise RuntimeError("No transcript found for this video.")
        except VideoUnavailable:
            raise RuntimeError("This video is unavailable.")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch transcript: {e}")
        
        #Store the transcript and meta data
        #Save this transcript in data base

        # if(database.store_transcript(video_id,full_text, video_meta_data)):
        #     print("Sucessfully stored the transcript in database.")
    
    else: 
        print("Video ID" + video_id)
        print("Video found in database.")

        full_text = database.get_transcript_from_db(video_id)
    return {"video_id": video_id, "text": full_text, 'video_meta_data': video_meta_data}

def translate_to_english(transcript: str, language: str) -> str:
    prompt = LANGUAGE_TRANSLATION_PROMPT.format(transcript=transcript, language=language)

    response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )
# returns as string 
    return response.text.strip()

#extract videos meta data using the package yt_dlp
def get_video_metadata(url: str) -> dict:
    """
    Given a YouTube URL, fetch and return the video metadata.
    """
    video_id = extract_video_id(url)
    ydl_opts = {
        'skip_download': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=False)
            return {
                "title": info_dict.get("title"),
                "description": info_dict.get("description"),
                "uploader": info_dict.get("uploader"),
                "upload_date": info_dict.get("upload_date"),
                "view_count": info_dict.get("view_count"),
                "like_count": info_dict.get("like_count"),
                "dislike_count": info_dict.get("dislike_count"),
                "duration": info_dict.get("duration"),
                "tags": info_dict.get("tags"),
            }
        except Exception as e:
            raise RuntimeError(f"Failed to fetch video metadata: {e}")


if __name__ == "__main__":
    test_url = input("Enter a YouTube URL: ").strip()
    print(get_transcript(test_url))

    #store in database done
    #retrive from database done

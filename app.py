"""
app.py

Flow:
Receive YouTube URL
    -> Call transcript module
    -> Receive transcript
    -> Print transcript
"""

from transcript import get_transcript
from topic_extractor import extract_topics
from internet_search import search_internet


def main():
    url = input("Enter a YouTube URL: ").strip()

    if not url:
        print("No URL provided. Exiting...")
        return

    try:
        transcript = get_transcript(url)
        topic = extract_topics(transcript)
        internet= search_internet(topic);
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")
        return

    print("\n--- Topics ---\n")
    print(topic)


if __name__ == "__main__":
    main()



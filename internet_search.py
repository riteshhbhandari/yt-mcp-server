from google import genai
from google.genai import types

from config import GEMINI_API_KEY, MODEL
from prompt import INTERNET_SEARCH_PROMPT
import json

client = genai.Client(api_key=GEMINI_API_KEY)

def search_internet(subject: str, topic: list):
    prompt = INTERNET_SEARCH_PROMPT.format(subject=subject, topic=topic)

    response = client.models.generate_content(
    model=MODEL,
    contents=prompt,
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(
                google_search=types.GoogleSearch()
            )
        ]
    )
    )
    print(response.text)
    return response.text

if __name__ == "__main__":
    result = search_internet (
        subject="Computer Organization and Architecture",
        topic=['Magnetic Disk Structure', 'Disk Capacity and Addressing', 'Disk Access Time (Seek Time, Rotational Latency, Transfer Time)', 'Cylinder-Head-Sector (CHS) Model', 'Memory Hierarchy', 'SRAM vs DRAM', 'DRAM Refresh and Organization', 'RAM and ROM Chips']
    )
    print(result)
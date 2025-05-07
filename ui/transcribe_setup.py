import asyncio
# This example uses aiofile for asynchronous file reads.
# It's not a dependency of the project but can be installed
# with `pip install aiofile`.
import aiofile
import os

from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

import subprocess

class MyEventHandler(TranscriptResultStreamHandler):
    def __init__(self, stream_output):
        super().__init__(stream_output)
        self.final_transcript = []

    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            if not result.is_partial:  # Correct way to check if it's final
                for alt in result.alternatives:
                    self.final_transcript.append(alt.transcript)

    async def handle_events(self):
        await super().handle_events()
        full_text = ' '.join(self.final_transcript)
        print("\nFinal Transcript:", full_text)

        return full_text


async def basic_transcribe(language_code):
    # Set up our client with your chosen Region
    client = TranscribeStreamingClient(region="ap-south-1")

    # Start transcription to generate async stream
    stream = await client.start_stream_transcription(
        language_code=language_code,
        media_sample_rate_hz=16000,
        media_encoding="pcm",
    )

    async def write_chunks():
        print("Sending audio chunks...")
        async with aiofile.AIOFile('Recording.pcm', 'rb') as afp:
            reader = aiofile.Reader(afp, chunk_size=1024 * 16)
            async for chunk in reader:
                await stream.input_stream.send_audio_event(audio_chunk=chunk)
        await stream.input_stream.end_stream()

    handler = MyEventHandler(stream.output_stream)

    # Get results from both coroutines
    results = await asyncio.gather(write_chunks(), handler.handle_events())
    
    # handler.handle_events() is the second coroutine, so it will be results[1]
    final_transcript = results[1]
    return final_transcript

def mp3_to_pcm(input_mp3, output_pcm):
    command = [
        "ffmpeg",
        "-y",                      # Overwrite output without asking
        "-i", input_mp3,          # Input MP3 file
        "-f", "s16le",            # Output format: PCM signed 16-bit little-endian
        "-acodec", "pcm_s16le",   # Audio codec
        "-ar", "16000",           # Sample rate
        "-ac", "1",               # Channels: 1 for mono
        output_pcm
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Conversion successful: {output_pcm}")
    except subprocess.CalledProcessError as e:
        print("Error during conversion:", e)


if __name__ == "__main__":
    final_text = asyncio.run(basic_transcribe())
    print("Returned Transcript:", final_text)


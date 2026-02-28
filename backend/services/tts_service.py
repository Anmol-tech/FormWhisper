# import os
# from dotenv import load_dotenv
# from elevenlabs.client import ElevenLabs
# # Change the import to target the utility function directly
# import elevenlabs.play as play



# load_dotenv()

# # Use the environment variable from your .env file
# client = ElevenLabs(
#     api_key=os.getenv("ELEVENLABS_API_KEY")
# )

# # Generate the audio
# audio_generator = client.text_to_speech.convert(
#     text="The first move is what sets everything in motion.",
#     voice_id="JBFqnCBsd6RMkjVDRZzb",
#     model_id="eleven_multilingual_v2",
#     output_format="mp3_44100_128",
# )

# # Convert the stream into a single playable block
# # This solves the 'TypeError' and 'Generator' issues
# audio_bytes = b"".join(list(audio_generator))
# play.play(audio_bytes)

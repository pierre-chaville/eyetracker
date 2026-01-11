import os
from dotenv import load_dotenv
from deepgram import DeepgramClient
from deepgram.listen import v1 as listen_v1
import threading
import time

# Load environment variables
load_dotenv()


def main():
    try:
        # Get Deepgram API key from environment
        api_key = os.getenv("DEEPGRAM_API_KEY")
        if not api_key:
            raise ValueError("DEEPGRAM_API_KEY not found in environment variables")

        # Initialize Deepgram client
        deepgram = DeepgramClient(api_key=api_key)

        print("Connecting to Deepgram... Start speaking in French when ready!")
        print("Press Ctrl+C to stop\n")

        # Event handlers
        def on_message(result, **kwargs):
            try:
                # Only print final results at endpointing
                if result.is_final:
                    sentence = result.channel.alternatives[0].transcript
                    if len(sentence) > 0:
                        print(sentence)
            except Exception as e:
                print(f"Error in on_message: {e}")

        def on_metadata(metadata, **kwargs):
            pass  # Silently handle metadata

        def on_speech_started(speech_started, **kwargs):
            pass  # Silent

        def on_utterance_end(utterance_end, **kwargs):
            pass  # Silent

        def on_error(error, **kwargs):
            print(f"Error: {error}")

        # Import microphone after connection is established
        try:
            import pyaudio
        except ImportError:
            print("PyAudio is not installed. Please install it first.")
            print("Run: pip install pyaudio")
            return

        # Create microphone stream
        CHUNK = 8192
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000

        audio = pyaudio.PyAudio()

        # List available input devices and try to open one
        print("Available audio input devices:")
        input_devices = []

        for i in range(audio.get_device_count()):
            device_info = audio.get_device_info_by_index(i)
            if device_info["maxInputChannels"] > 0:
                print(
                    f"  [{i}] {device_info['name']} (Input channels: {device_info['maxInputChannels']}, Sample rate: {int(device_info['defaultSampleRate'])})"
                )
                input_devices.append((i, device_info))

        if not input_devices:
            print("\nNo input devices found! Please check your microphone connection.")
            audio.terminate()
            return

        # Try to open devices one by one until one works
        stream = None
        for device_index, device_info in input_devices:
            try:
                print(f"\nTrying device [{device_index}]: {device_info['name']}...")

                # Try with device's native sample rate first, then fall back to 16000
                for sample_rate in [
                    int(device_info["defaultSampleRate"]),
                    16000,
                    44100,
                    48000,
                ]:
                    try:
                        stream = audio.open(
                            format=FORMAT,
                            channels=CHANNELS,
                            rate=sample_rate,
                            input=True,
                            input_device_index=device_index,
                            frames_per_buffer=CHUNK,
                        )
                        RATE = sample_rate
                        print(f"✓ Successfully opened device at {sample_rate} Hz\n")
                        break
                    except Exception as e:
                        if sample_rate == 48000:  # Last attempt
                            raise
                        continue

                if stream:
                    break

            except Exception as e:
                print(f"  Failed: {e}")
                continue

        if stream is None:
            print(
                "\nCould not open any audio input device. Please check your microphone settings."
            )
            audio.terminate()
            return

        print("Microphone is active. Connecting to Deepgram...")

        # Create live transcription connection with options (use actual sample rate)
        with deepgram.listen.v1.connect(
            model="nova-2",
            language="fr",
            punctuate="true",
            encoding="linear16",
            channels="1",
            sample_rate=str(RATE),
            interim_results="true",
            endpointing="2000",
            vad_events="true",
        ) as dg_connection:
            # Register event handlers
            dg_connection.on(listen_v1.ListenV1Results, on_message)
            dg_connection.on(listen_v1.ListenV1Metadata, on_metadata)
            dg_connection.on(listen_v1.ListenV1SpeechStarted, on_speech_started)
            dg_connection.on(listen_v1.ListenV1UtteranceEnd, on_utterance_end)

            print("Connected! Start speaking in French...\n")

            # Flag to control the loop
            running = True

            # Function to receive messages from Deepgram
            def receive_messages():
                while running:
                    try:
                        message = dg_connection.recv()
                        if isinstance(message, listen_v1.ListenV1Results):
                            on_message(message)
                        elif isinstance(message, listen_v1.ListenV1Metadata):
                            on_metadata(message)
                        elif isinstance(message, listen_v1.ListenV1SpeechStarted):
                            on_speech_started(message)
                        elif isinstance(message, listen_v1.ListenV1UtteranceEnd):
                            on_utterance_end(message)
                    except Exception as e:
                        if running:
                            print(f"Error receiving message: {e}")
                        break

            # Start receiving messages in a separate thread
            receive_thread = threading.Thread(target=receive_messages, daemon=True)
            receive_thread.start()

            # Give the connection a moment to fully establish
            time.sleep(0.1)

            # Stream audio to Deepgram
            try:
                while True:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    dg_connection.send_media(data)
            except KeyboardInterrupt:
                print("\n\nStopping transcription...")
                running = False

        # Cleanup
        stream.stop_stream()
        stream.close()
        audio.terminate()

        print("Transcription stopped.")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

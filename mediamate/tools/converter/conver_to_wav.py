import subprocess
import os


class AudioExtractor:
    def __init__(self, output_dir: str = "extracted_audio"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_audio(self, video_file: str) -> str:
        """Extract audio from a video file and save it as a WAV file using ffmpeg."""
        try:
            # Generate output file path by replacing the extension with .wav
            base_name = os.path.basename(video_file)
            output_file = os.path.join(self.output_dir, f"{os.path.splitext(base_name)[0]}.wav")

            # Construct ffmpeg command
            command = [
                'ffmpeg',
                '-i', video_file,  # Input file
                '-vn',  # Disable video recording
                '-acodec', 'pcm_s16le',  # Audio codec (WAV format)
                '-ar', '44100',  # Audio sampling rate
                '-ac', '2',  # Audio channels
                output_file  # Output file
            ]

            # Run the command
            subprocess.run(command, check=True)

            return output_file
        except subprocess.CalledProcessError as e:
            return f"Error extracting audio: {e}"
        except Exception as e:
            return str(e)

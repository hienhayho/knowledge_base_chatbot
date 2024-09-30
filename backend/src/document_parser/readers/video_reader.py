import os
import re
import json
import tempfile
import asyncio
from typing import List, Dict
from moviepy.editor import VideoFileClip
import google.generativeai as genai
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment
import aiofiles
import aiofiles.os
from openai.resources.audio.transcriptions import Transcription
from src.constants import GlobalConfig
import logging
from .prompts import VIDEO_PROCESSING_PROMPT
from llama_index.core.schema import Document

load_dotenv()


class VideoReader:
    def __init__(self):
        self.GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
        self.OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
        genai.configure(api_key=self.GOOGLE_API_KEY)
        self.gemini_model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
        self.openai_client = OpenAI(api_key=self.OPENAI_API_KEY)
        self.max_concurrent_requests = GlobalConfig.MAX_CONCURRENT_REQUESTS
        self.output_dir = GlobalConfig.UPLOAD_FOLDER

    async def load_data(self, video_path: str) -> List[Dict]:
        logging.info(f"Processing video: {video_path}")
        audio_path = await self._aextract_audio(video_path)
        logging.info("Audio extraction complete.")

        audio_chunk_filepaths = await self._asplit_audio(audio_path)
        logging.info(f"Audio split into {len(audio_chunk_filepaths)} chunks.")

        transcript = await self._atranscribe_and_combine(audio_chunk_filepaths)
        logging.info("Transcription complete.")

        summary = await self._get_summary(audio_path)
        logging.info("Summary generation complete.")

        sections = self._process_sections(summary, transcript)
        logging.info("Sections processed.")

        # await asyncio.to_thread(self._cut_video_sections, video_path, sections)

        # Clean up
        await self.__cleanup_resources(audio_path, audio_chunk_filepaths)
        logging.info("Temporary files removed.")

        return [
            Document(
                text=section["text"],
                metadata={**section["metadata"], "video_path": video_path},
            )
            for section in sections
        ]

    async def _aextract_audio(self, video_file_path: str) -> str:
        logging.info("Extracting audio from video...")
        output_audio_path = tempfile.mktemp(suffix=".wav")
        video_clip = VideoFileClip(video_file_path)
        await asyncio.to_thread(
            video_clip.audio.write_audiofile,
            output_audio_path,
            verbose=False,
            logger=None,
        )
        video_clip.close()
        logging.info("Audio extraction complete.")
        return output_audio_path

    async def _asplit_audio(
        self, audio_file_path: str, chunk_duration_ms: int = 100 * 1000
    ) -> List[str]:
        logging.info("Splitting audio into chunks...")
        audio_segment = AudioSegment.from_wav(audio_file_path)
        chunk_file_paths = []
        for start_time in range(0, len(audio_segment), chunk_duration_ms):
            audio_chunk = audio_segment[start_time : start_time + chunk_duration_ms]
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".wav"
            ) as temp_chunk_file:
                chunk_file_path = temp_chunk_file.name
                audio_chunk.export(chunk_file_path, format="wav")
                chunk_file_paths.append(chunk_file_path)
        logging.info(f"Audio split into {len(chunk_file_paths)} chunks.")
        return chunk_file_paths

    async def _atranscribe_audio(self, audio_file_path: str) -> Transcription | str:
        def sync_transcribe(audio_file_path: str) -> Transcription:
            with open(audio_file_path, "rb") as audio_file:
                transcription_result: Transcription = (
                    self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",
                        timestamp_granularities=["segment", "word"],
                    )
                )
                return transcription_result

        if asyncio.get_event_loop().is_running():
            transcription_result = await asyncio.to_thread(
                sync_transcribe, audio_file_path
            )
        else:
            transcription_result = sync_transcribe(audio_file_path)

        return transcription_result

    async def _atranscribe_and_combine(
        self, audio_chunk_filepaths: List[str]
    ) -> List[Dict]:
        logging.info("Starting transcription process...")
        transcript_tasks = [
            self._atranscribe_audio(chunk) for chunk in audio_chunk_filepaths
        ]
        transcript_responses = await asyncio.gather(*transcript_tasks)

        full_transcript_with_timestamp = []
        offset = 0
        for response in transcript_responses:
            for segment in response.segments:
                segment["start"] += offset
                segment["end"] += offset
                full_transcript_with_timestamp.append(
                    {
                        "text": segment["text"],
                        "start": self._format_time(segment["start"]),
                        "end": self._format_time(segment["end"]),
                    }
                )
            offset = self._time_to_seconds(full_transcript_with_timestamp[-1]["end"])

        logging.info("Transcription and combination complete.")
        return full_transcript_with_timestamp

    async def _get_summary(self, audio_path: str) -> Dict:
        logging.info("Starting summary generation...")
        video_file = await asyncio.to_thread(genai.upload_file, path=audio_path)
        logging.info("Audio file uploaded for summarization.")

        prompt = VIDEO_PROCESSING_PROMPT

        response = await asyncio.to_thread(
            self.gemini_model.generate_content,
            [prompt, video_file],
            request_options={"timeout": 3000},
        )
        logging.info("Summary generation complete.")

        # Extract JSON string from the input
        json_str = re.search(r"```json\n(.*?)```", response.text, re.DOTALL)
        if json_str:
            json_str = json_str.group(1)
        else:
            raise ValueError("No JSON string found in the input")
        logging.info(json_str)
        return json.loads(json_str)

    def _process_sections(
        self, summary_data: Dict, transcript: List[Dict]
    ) -> List[Dict]:
        logging.info("Processing video sections...")
        processed_sections = []
        for i, section in enumerate(summary_data["sections"]):
            section_start = self._time_to_seconds(section["start_time"])
            section_end = self._time_to_seconds(section["end_time"])

            section_transcript = [
                entry
                for entry in transcript
                if section_start <= self._time_to_seconds(entry["start"]) < section_end
            ]

            processed_section = {
                "text": section["summary"],
                "metadata": {
                    "video_summary": summary_data["summary"],
                    "start_time": section["start_time"],
                    "end_time": section["end_time"],
                    "transcript": " ".join(
                        entry["text"] for entry in section_transcript
                    ),
                },
            }
            processed_sections.append(processed_section)
        logging.info("Section processing complete.")
        return processed_sections

    def _cut_video_sections(self, video_path: str, sections: List[Dict]):
        logging.info("Cutting video into sections...")
        video = VideoFileClip(video_path)

        video_name = os.path.splitext(os.path.basename(video_path))[0]

        for i, section in enumerate(sections):

            logging.info(f"Cutting section {i+1}/{len(sections)}")
            start_time = self._time_to_seconds(section["metadata"]["start_time"])
            end_time = self._time_to_seconds(section["metadata"]["end_time"])

            section_clip = video.subclip(start_time, end_time)
            output_path = f"{self.output_dir}/{video_name}_section_{i+1}.mp4"
            section_clip.write_videofile(output_path, verbose=False, logger=None)

            section["metadata"]["section_path"] = output_path

        video.close()
        logging.info("Video cutting complete.")

    async def __cleanup_resources(
        self, audio_path: str, audio_chunk_filepaths: List[str]
    ):
        logging.info("Cleaning up temporary files...")
        await aiofiles.os.remove(audio_path)
        cleanup_tasks = [aiofiles.os.remove(chunk) for chunk in audio_chunk_filepaths]
        await asyncio.gather(*cleanup_tasks)
        logging.info("Cleanup complete.")

    @staticmethod
    def _time_to_seconds(time_str: str) -> float:
        time_parts = time_str.split(":")
        if len(time_parts) == 2:  # MM:SS format
            return int(time_parts[0]) * 60 + float(time_parts[1])
        elif len(time_parts) == 3:  # HH:MM:SS format
            return (
                int(time_parts[0]) * 3600
                + int(time_parts[1]) * 60
                + float(time_parts[2])
            )
        else:
            raise ValueError(f"Invalid time format: {time_str}")

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Convert seconds to hours, minutes and seconds.

        Args:
            seconds (float): The time in seconds.

        Returns:
            str: The time in the format HH:MM:SS.
        """
        minutes = int(seconds // 60)
        hours = int(minutes // 60)
        remaining_minutes = int(minutes % 60)
        remaining_seconds = int(seconds % 60)
        return f"{hours:02}:{remaining_minutes:02}:{remaining_seconds:02}"


# Usage example:
async def main():
    video_reader = VideoReader()
    results = await video_reader.load_data(
        "/home/bachngo/Desktop/code/Knowledge_Base_Agent/backend/notebooks/video_data/input_vid.mp4"
    )
    for i, section in enumerate(results, 1):
        logging.info(f"Section {i}:")
        logging.info(f"Summary: {section['text']}")
        logging.info(f"Start Time: {section['metadata']['start_time']}")
        logging.info(f"End Time: {section['metadata']['end_time']}")
        logging.info(f"Section Video Path: {section['metadata']['section_path']}")
        logging.info(f"Transcript: {section['metadata']['transcript'][:100]}...")
        logging.info("---")


if __name__ == "__main__":
    asyncio.run(main())

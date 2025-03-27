import os
from typing import BinaryIO, Dict, Optional, Tuple, Union
from datetime import date, datetime, timezone
import assemblyai as aai
from .models import Meeting
from .repository import MeetingRepository, TranscriptRepository


class MeetingService:
    def __init__(self, db_session):
        self.db = db_session
        aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        aai.settings.base_url = os.getenv("ASSEMBLYAI_BASE_URL", "https://api.eu.assemblyai.com")

    def transcribe_meeting(
        self,
        uploaded_file: str | BinaryIO,
        meeting_name: str,
        meeting_date: Optional[date] = None,
    ) -> str:
        """
        Transcribe an audio file and store the meeting in the database.

        Args:
            uploaded_file: Path to the audio file to transcribe.
            meeting_name: Name of the meeting.
            meeting_date: Optional date or tuple of dates for the meeting.

        Returns:
            The ID of the transcribed meeting.
        """
        transcript = TranscriptionService().transcribe_audio(uploaded_file)
        if not transcript.id or not transcript.text:
            print("Transcription failed.")
            return ""

        meeting_id: str = transcript.id

        # Store the meeting in the database
        meeting = Meeting(
            id=meeting_id,
            name=meeting_name,
            date=meeting_date,
            created=datetime.now(timezone.utc),
            status="transcribed",
            deleted=None,
        )
        self.db.add(meeting)
        self.db.commit()

        # Store the transcript in the database
        transcript_text = TranscriptionService.format_transcript(transcript)
        TranscriptRepository.insert_or_update(
            db=self.db, meeting_id=meeting_id, text=transcript.text, transcript=transcript_text
        )

        return meeting_id

    def sync_meetings(self, include_remote: bool = False) -> Dict[str, Meeting]:
        local_meetings = MeetingRepository.get_all(self.db)

        if include_remote:
            remote_meetings = self._fetch_remote_meetings()
            self._merge_meetings(local_meetings, remote_meetings)

        return local_meetings

    def _fetch_remote_meetings(self) -> Dict[str, Meeting]:
        transcripts: Dict[str, Meeting] = {}
        already_processed = set()
        try:
            transcriber = aai.Transcriber()
            params = aai.ListTranscriptParameters()
            page = transcriber.list_transcripts(params)
            while page.transcripts:
                transcripts |= {
                    t.id: Meeting(
                        id=t.id,
                        created=(datetime.fromisoformat(t.created) if t.created else None),
                        status=t.status.name,
                    )
                    for t in page.transcripts
                    if t.audio_url != "http://deleted_by_user"
                }
                if (
                    not page.page_details.before_id_of_prev_url
                    or page.page_details.before_id_of_prev_url in already_processed
                ):
                    break
                params.before_id = page.page_details.before_id_of_prev_url
                already_processed.update({page.page_details.before_id_of_prev_url})
                page = transcriber.list_transcripts(params)
            return transcripts
        except Exception as e:
            raise RuntimeError(f"Failed to fetch remote meetings: {str(e)}") from e

    def _merge_meetings(self, local: Dict[str, Meeting], remote: Dict[str, Meeting]) -> None:
        """
        Merge remote meetings into local meetings and update the database.

        Args:
            local: Dictionary of local meetings (key: meeting ID, value: Meeting object).
            remote: Dictionary of remote meetings (key: meeting ID, value: Meeting object).
        """
        try:
            local_transcripts = TranscriptRepository.get_all(self.db)
            for meeting_id, remote_meeting in remote.items():
                if meeting_id in local:
                    # Update existing meeting with remote data
                    local_meeting = local[meeting_id]
                    local_meeting.created = remote_meeting.created
                    local_meeting.status = remote_meeting.status
                else:
                    # Add new remote meeting to local database
                    new_meeting = MeetingRepository.insert_or_update(
                        self.db,
                        meeting_id=meeting_id,
                        name="",  # Default name, can be updated later
                        meeting_date=None,  # Default date, can be updated later
                        created=remote_meeting.created,
                        status=remote_meeting.status,
                        deleted=None,
                    )
                    local[meeting_id] = new_meeting
                if meeting_id not in local_transcripts:
                    # Add new transcript for remote meeting
                    remote_transcript = TranscriptionService().get_transcript(meeting_id)
                    TranscriptRepository.insert_or_update(
                        db=self.db,
                        meeting_id=meeting_id,
                        text=remote_transcript.text or "",
                        transcript=TranscriptionService.format_transcript(remote_transcript),
                    )

            # Commit changes to the database
            self.db.commit()
        except Exception as e:
            self.db.rollback()  # Rollback en cas d'erreur
            raise RuntimeError(f"Failed to merge meetings: {str(e)}") from e

    @staticmethod
    def _format_meeting_date(meeting_date: Optional[date]) -> Optional[datetime]:
        """
        Format the meeting date from various input types.

        Args:
            meeting_date: A datetime, a tuple of datetimes, or None.

        Returns:
            A single datetime or None.
        """
        if isinstance(meeting_date, tuple):
            return meeting_date[0] if meeting_date and meeting_date[0] else None
        if meeting_date:
            return datetime.combine(meeting_date, datetime.min.time())
        return None


class TranscriptionService:
    def __init__(self):
        aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        aai.settings.base_url = os.getenv("ASSEMBLYAI_BASE_URL", "https://api.eu.assemblyai.com")

    def transcribe_audio(self, file: str | BinaryIO) -> aai.Transcript:
        config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.best, speaker_labels=True, language_detection=True
        )
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(file)
        return transcript

    def lemur_task(self, meeting_id: str, prompt: str) -> str:
        transcript = aai.Transcript.get_by_id(meeting_id)
        result = transcript.lemur.task(prompt, final_model=aai.LemurModel.claude3_5_sonnet)
        return result.response

    @staticmethod
    def get_transcript(transcript_id: str) -> aai.Transcript:
        return aai.Transcript.get_by_id(transcript_id)

    @staticmethod
    def format_transcript(transcript) -> str:
        return "\n".join(f"[Speaker {utterance.speaker}] {utterance.text}" for utterance in transcript.utterances)

    @staticmethod
    def delete_transcript(transcript_id: str) -> None:
        aai.Transcript.delete_by_id(transcript_id)

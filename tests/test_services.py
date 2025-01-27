import pytest
from datetime import datetime, timezone, date
from unittest.mock import Mock, patch
from meeting_minutes.services import MeetingService, TranscriptionService
from meeting_minutes.models import Meeting


@pytest.fixture
def db_session():
    return Mock()


@pytest.fixture
def meeting_service(db_session):
    return MeetingService(db_session)


def test_transcribe_meeting(meeting_service):
    # Mock dependencies
    with patch("meeting_minute.services.TranscriptionService") as mock_transcription:
        mock_transcript = Mock()
        mock_transcript.id = "test_id"
        mock_transcript.text = "test transcript"
        mock_transcription.return_value.transcribe_audio.return_value = mock_transcript

        # Test transcribe_meeting
        meeting_id = meeting_service.transcribe_meeting("test.mp3", "Test Meeting", date(2024, 1, 1))

        assert meeting_id == "test_id"


def test_sync_meetings(meeting_service):
    # Mock local meetings
    local_meetings = {"1": Meeting(id="1", name="Meeting 1"), "2": Meeting(id="2", name="Meeting 2")}

    with patch("meeting_minute.repository.MeetingRepository") as mock_repo:
        mock_repo.get_all.return_value = list(local_meetings.values())

        # Test without remote sync
        result = meeting_service.sync_meetings(include_remote=False)
        assert result == local_meetings


def test_format_meeting_date():
    # Test with date
    test_date = date(2024, 1, 1)
    result = MeetingService._format_meeting_date(test_date)
    assert isinstance(result, datetime)
    assert result.date() == test_date

    # Test with None
    assert MeetingService._format_meeting_date(None) is None

    # Test with tuple
    date_tuple = (datetime(2024, 1, 1), datetime(2024, 1, 2))
    result = MeetingService._format_meeting_date(date_tuple)
    assert result == date_tuple[0]


def test_merge_meetings(meeting_service):
    local = {"1": Meeting(id="1", name="Local Meeting")}
    remote = {
        "1": Meeting(id="1", status="completed", created=datetime.now()),
        "2": Meeting(id="2", status="processing", created=datetime.now()),
    }

    meeting_service._merge_meetings(local, remote)

    assert "1" in local
    assert local["1"].status == "completed"

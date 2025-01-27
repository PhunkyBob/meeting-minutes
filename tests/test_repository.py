import pytest
from datetime import datetime, date, timezone
from meeting_minutes.models import Meeting, Prompt, Query, Transcript
from meeting_minutes.repository import MeetingRepository, PromptRepository, QueryRepository, TranscriptRepository
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Meeting.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_meeting_get_all(db_session):
    # Arrange
    meeting = Meeting(id="test-id", name="Test Meeting", date=date.today(), created=datetime.now(), status="pending")
    db_session.add(meeting)
    db_session.commit()

    # Act
    result = MeetingRepository.get_all(db_session)

    # Assert
    assert len(result) == 1
    assert "test-id" in result
    assert result["test-id"].name == "Test Meeting"


def test_meeting_soft_delete(db_session):
    # Arrange
    meeting_id = "test-id"
    meeting = Meeting(id=meeting_id, name="Test Meeting", status="pending")
    db_session.add(meeting)
    db_session.commit()

    # Act
    MeetingRepository.soft_delete(db_session, meeting_id)

    # Assert
    result = MeetingRepository.get_all(db_session)
    assert len(result) == 0


def test_meeting_insert_or_update(db_session):
    # Arrange
    meeting_id = "test-id"
    name = "Test Meeting"
    meeting_date = date.today()
    created = datetime.now(timezone.utc)
    status = "pending"

    # Act - Insert
    meeting = MeetingRepository.insert_or_update(db_session, meeting_id, name, meeting_date, created, status)

    # Assert
    assert meeting.id == meeting_id
    assert meeting.name == name

    # Act - Update
    new_name = "Updated Meeting"
    updated = MeetingRepository.insert_or_update(db_session, meeting_id, new_name, meeting_date, created, status)

    # Assert
    assert updated.id == meeting_id
    assert updated.name == new_name


def test_transcript_store_and_get(db_session):
    # Arrange
    meeting_id = "test-id"
    text = "Original text"
    transcript = "Transcribed text"

    # Act - Store
    stored = TranscriptRepository.store_transcript(db_session, meeting_id, text, transcript)

    # Assert store
    assert stored.meeting == meeting_id
    assert stored.text == text
    assert stored.transcript == transcript

    # Act - Get
    retrieved = TranscriptRepository.get_transcript(db_session, meeting_id)

    # Assert get
    assert retrieved is not None
    assert retrieved.meeting == meeting_id
    assert retrieved.text == text
    assert retrieved.transcript == transcript


def test_transcript_get_nonexistent(db_session):
    # Act
    result = TranscriptRepository.get_transcript(db_session, "nonexistent-id")

    # Assert
    assert result is None


def test_transcript_get_all(db_session):
    # Arrange
    meeting_id = "test-id"
    transcript = Transcript(meeting=meeting_id, text="Original text", transcript="Transcribed text")
    db_session.add(transcript)
    db_session.commit()

    # Act
    result = TranscriptRepository.get_all(db_session)

    # Assert
    assert len(result) == 1
    assert meeting_id in result
    assert result[meeting_id].text == "Original text"
    assert result[meeting_id].transcript == "Transcribed text"


def test_transcript_soft_delete(db_session):
    # Arrange
    meeting_id = "test-id"
    transcript = Transcript(meeting=meeting_id, text="Original text", transcript="Transcribed text")
    db_session.add(transcript)
    db_session.commit()

    # Act
    TranscriptRepository.soft_delete(db_session, meeting_id)

    # Assert
    result = TranscriptRepository.get_all(db_session)
    assert len(result) == 0

    # Verify soft deleted transcript is included when include_deleted=True
    result_with_deleted = TranscriptRepository.get_all(db_session, include_deleted=True)
    assert len(result_with_deleted) == 1
    assert result_with_deleted[meeting_id].deleted is not None


def test_prompt_get_all(db_session):
    # Arrange
    prompt = Prompt(name="Test Prompt", prompt="Test prompt text")
    db_session.add(prompt)
    db_session.commit()

    # Act
    result = PromptRepository.get_all(db_session)

    # Assert
    assert len(result) == 1
    assert 1 in result
    assert result[1].name == "Test Prompt"


def test_prompt_get_by_id(db_session):
    # Arrange
    prompt = Prompt(name="Test Prompt", prompt="Test prompt text")
    db_session.add(prompt)
    db_session.commit()

    # Act
    result = PromptRepository.get_by_id(db_session, 1)

    # Assert
    assert result is not None
    assert result.name == "Test Prompt"


def test_prompt_get_by_name(db_session):
    # Arrange
    prompt = Prompt(name="Test Prompt", prompt="Test prompt text")
    db_session.add(prompt)
    db_session.commit()

    # Act
    result = PromptRepository.get_by_name(db_session, "Test Prompt")

    # Assert
    assert result is not None
    assert result.prompt == "Test prompt text"


def test_prompt_create(db_session):
    # Act
    prompt = PromptRepository.create(db_session, "New Prompt", "New prompt text")

    # Assert
    assert prompt.name == "New Prompt"
    assert prompt.prompt == "New prompt text"


def test_prompt_update(db_session):
    # Arrange
    prompt = Prompt(name="Test Prompt", prompt="Test prompt text")
    db_session.add(prompt)
    db_session.commit()

    # Act
    updated = PromptRepository.update(db_session, 1, "Updated Prompt", "Updated text")

    # Assert
    assert updated.name == "Updated Prompt"
    assert updated.prompt == "Updated text"


def test_prompt_soft_delete(db_session):
    # Arrange
    prompt = Prompt(name="Test Prompt", prompt="Test prompt text")
    db_session.add(prompt)
    db_session.commit()

    # Act
    PromptRepository.soft_delete(db_session, 1)

    # Assert
    result = PromptRepository.get_all(db_session)
    assert len(result) == 0


def test_query_get_by_meeting(db_session):
    # Arrange
    meeting_id = "test-id"
    query = Query(meeting=meeting_id, question="Test question", answer="Test answer")
    db_session.add(query)
    db_session.commit()

    # Act
    result = QueryRepository.get_by_meeting(db_session, meeting_id)

    # Assert
    assert len(result) == 1
    assert 1 in result
    assert result[1].question == "Test question"
    assert result[1].answer == "Test answer"


def test_query_store_query(db_session):
    # Arrange
    meeting_id = "test-id"
    question = "Test question"
    answer = "Test answer"

    # Act
    result = QueryRepository.store_query(db_session, meeting_id, question, answer)

    # Assert
    assert result.meeting == meeting_id
    assert result.question == question
    assert result.answer == answer


def test_query_soft_delete(db_session):
    # Arrange
    meeting_id = "test-id"
    query = Query(meeting=meeting_id, question="Test question", answer="Test answer")
    db_session.add(query)
    db_session.commit()

    # Act
    QueryRepository.soft_delete(db_session, 1)

    # Assert
    result = QueryRepository.get_by_meeting(db_session, meeting_id)
    assert len(result) == 0


def test_query_get_all_history(db_session):
    # Arrange
    meeting_id = "test-id"
    query = Query(meeting=meeting_id, question="Test question", answer="Test answer")
    db_session.add(query)
    db_session.commit()

    # Soft delete the query
    QueryRepository.soft_delete(db_session, 1)

    # Act
    result = QueryRepository.get_all_history(db_session, meeting_id)

    # Assert
    assert len(result) == 1
    assert 1 in result
    assert result[1].question == "Test question"
    assert result[1].deleted is not None

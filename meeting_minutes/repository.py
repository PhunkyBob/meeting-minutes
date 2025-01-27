from sqlalchemy.orm import Session
from datetime import date, datetime, timezone
from typing import Dict, Optional
from .models import Meeting, Prompt, Query, Transcript


class MeetingRepository:
    @staticmethod
    def get_all(db: Session, include_deleted: bool = False) -> Dict[str, Meeting]:
        query = db.query(Meeting)
        if not include_deleted:
            query = query.filter(Meeting.deleted.is_(None))
        return {meeting.id: meeting for meeting in query.all()}

    @staticmethod
    def soft_delete(db: Session, meeting_id: str) -> None:
        db.query(Meeting).filter(Meeting.id == meeting_id).update({"deleted": datetime.now()})
        db.query(Query).filter(Query.meeting == meeting_id).update({"deleted": datetime.now()})
        db.query(Transcript).filter(Transcript.meeting == meeting_id).update({"deleted": datetime.now()})
        db.commit()

    @staticmethod
    def insert_or_update(
        db: Session,
        meeting_id: str,
        name: str,
        meeting_date: Optional[date],
        created: datetime,
        status: str,
        deleted: Optional[datetime] = None,
    ) -> Meeting:
        existing = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if existing:
            existing.name = name
            existing.date = meeting_date
            existing.created = created
            existing.status = status
            existing.deleted = deleted
        else:
            existing = Meeting(
                id=meeting_id, name=name, date=meeting_date, created=created, status=status, deleted=deleted
            )
            db.add(existing)

        db.commit()
        db.refresh(existing)
        return existing


class TranscriptRepository:
    @staticmethod
    def insert_or_update(
        db: Session, meeting_id: str, text: str, transcript: str, deleted: Optional[datetime] = None
    ) -> Transcript:
        existing = db.query(Transcript).filter(Transcript.meeting == meeting_id).first()
        if existing:
            existing.text = text
            existing.transcript = transcript
            existing.deleted = deleted
        else:
            existing = Transcript(meeting=meeting_id, text=text, transcript=transcript, deleted=deleted)
            db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    @staticmethod
    def get_transcript(db: Session, meeting_id: str) -> Optional[Transcript]:
        return db.query(Transcript).filter(Transcript.meeting == meeting_id).first()

    @staticmethod
    def get_all(db: Session, include_deleted: bool = False) -> Dict[str, Transcript]:
        query = db.query(Transcript)
        if not include_deleted:
            query = query.filter(Transcript.deleted.is_(None))
        return {transcript.meeting: transcript for transcript in query.all()}

    @staticmethod
    def soft_delete(db: Session, meeting_id: str) -> None:
        db.query(Transcript).filter(Transcript.meeting == meeting_id).update({"deleted": datetime.now()})
        db.commit()


class PromptRepository:
    @staticmethod
    def get_all(db: Session, include_deleted: bool = False) -> Dict[int, Prompt]:
        """Retrieve all prompts from database"""
        query = db.query(Prompt)
        if not include_deleted:
            query = query.filter(Prompt.deleted.is_(None))
        return {prompt.id: prompt for prompt in query.all()}

    @staticmethod
    def get_by_id(db: Session, prompt_id: int) -> Optional[Prompt]:
        """Get a single prompt by its ID"""
        return db.query(Prompt).filter(Prompt.id == prompt_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Prompt]:
        """Find prompt by its name"""
        return db.query(Prompt).filter(Prompt.name == name).first()

    @staticmethod
    def create(db: Session, name: str, prompt_text: str) -> Prompt:
        prompt = Prompt(name=name, prompt=prompt_text)
        db.add(prompt)

        db.commit()
        db.refresh(prompt)
        return prompt

    @staticmethod
    def update(db: Session, id: int, name: str, prompt_text: str) -> Prompt:
        """Update operation for prompts"""
        existing = db.query(Prompt).filter(Prompt.id == id).first()
        if not existing:
            raise ValueError(f"Prompt with ID {id} not found")
        existing.name = name
        existing.prompt = prompt_text

        db.commit()
        db.refresh(existing)
        return existing

    @staticmethod
    def soft_delete(db: Session, prompt_id: int) -> None:
        """Mark prompt as deleted"""
        db.query(Prompt).filter(Prompt.id == prompt_id).update({"deleted": datetime.now()})
        db.commit()


class QueryRepository:
    @staticmethod
    def get_by_meeting(db: Session, meeting_id: str) -> Dict[int, Query]:
        """Get all queries for a specific meeting"""
        return {
            query.id: query
            for query in db.query(Query)
            .filter(Query.meeting == meeting_id)
            .filter(Query.deleted.is_(None))
            .order_by(Query.created.desc())
            .all()
        }

    @staticmethod
    def store_query(
        db: Session, meeting_id: str, question: str, answer: str, created: Optional[datetime] = None
    ) -> Query:
        """Persist new query in database"""
        if not created:
            created = datetime.now()
        new_query = Query(meeting=meeting_id, question=question, answer=answer, created=created)
        db.add(new_query)
        db.commit()
        db.refresh(new_query)
        return new_query

    @staticmethod
    def update_query(
        db: Session, query_id: int, question: Optional[str] = None, answer: Optional[str] = None
    ) -> Query:
        """Update query in database"""
        existing = db.query(Query).filter(Query.id == query_id).first()
        if not existing:
            raise ValueError(f"Query with ID {query_id} not found")
        if question:
            existing.question = question
        if answer:
            existing.answer = answer

        db.commit()
        db.refresh(existing)
        return existing

    @staticmethod
    def soft_delete(db: Session, query_id: int) -> None:
        """Mark query as deleted"""
        db.query(Query).filter(Query.id == query_id).update({"deleted": datetime.now()})
        db.commit()

    @staticmethod
    def get_all_history(db: Session, meeting_id: str) -> Dict[int, Query]:
        """Retrieve full history including deleted queries"""
        return {
            query.id: query
            for query in db.query(Query).filter(Query.meeting == meeting_id).order_by(Query.created.desc()).all()
        }

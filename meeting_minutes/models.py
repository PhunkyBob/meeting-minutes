# models.py
from typing import Optional
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base
from datetime import datetime, timezone, date as datetime_date


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    date: Mapped[Optional[datetime_date]] = mapped_column(Date, nullable=True)
    created: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=True)
    deleted: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    transcripts_rel: Mapped[list["Transcript"]] = relationship(back_populates="meeting_rel")
    queries_rel: Mapped[list["Query"]] = relationship(back_populates="meeting_rel")


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text)
    prompt: Mapped[str] = mapped_column(Text)
    deleted: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Query(Base):
    __tablename__ = "queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meeting: Mapped[str] = mapped_column(ForeignKey("meetings.id"))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    deleted: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    meeting_rel: Mapped["Meeting"] = relationship(back_populates="queries_rel")


class Transcript(Base):
    __tablename__ = "transcripts"

    meeting: Mapped[str] = mapped_column(ForeignKey("meetings.id"), primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    transcript: Mapped[str] = mapped_column(Text)
    deleted: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    meeting_rel: Mapped["Meeting"] = relationship(back_populates="transcripts_rel")

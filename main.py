from typing import Dict
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
import pandas as pd
from sqlalchemy.orm import Session

from meeting_minutes import tab_history, tab_new, tab_prompts
from datetime import date
from meeting_minutes.database import init_db, get_db
from meeting_minutes.models import Meeting, Prompt
from meeting_minutes.repository import MeetingRepository, PromptRepository, QueryRepository, TranscriptRepository
from meeting_minutes.services import MeetingService, TranscriptionService

st.session_state["tabs"] = st.session_state.get("tabs", None)
st.set_page_config(layout="wide")


def main() -> None:
    init_db()
    db: Session = next(get_db())

    st.title("Meeting Minutes")

    tab1, tab2, tab3 = st.tabs(["Nouvelle réunion", "Historique", "Prompts prédéfinis"])
    meeting_service = MeetingService(db)
    transcription_service = TranscriptionService()

    with tab1:
        tab_new.tab_new(meeting_service)

    with tab2:
        tab_history.tab_history(db, meeting_service, transcription_service)

    with tab3:
        tab_prompts.tab_prompts(db)


if __name__ == "__main__":
    main()

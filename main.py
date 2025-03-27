import os
import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from meeting_minutes import tab_history, tab_new, tab_prompts
from meeting_minutes.database import init_db, get_db
from meeting_minutes.services import MeetingService, TranscriptionService
from meeting_minutes.tabs import Tab

st.session_state["tabs"] = st.session_state.get("tabs", Tab.NEW_MEETING.value)
st.set_page_config(layout="wide")


def main() -> None:
    load_dotenv()
    init_db()
    db: Session = next(get_db())

    st.title("Meeting Minutes")

    tab1, tab2, tab3 = st.tabs([Tab.NEW_MEETING.value, Tab.HISTORY.value, Tab.PROMPTS.value])
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

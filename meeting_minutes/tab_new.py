import streamlit as st
from datetime import date

from meeting_minutes.tabs import Tab


def tab_new(meeting_service):
    st.header("Nouvelle réunion")
    if st.session_state.get("reset_form", False):
        meeting_name = st.text_input("Nom de la réunion", value=" ")
        st.session_state["reset_form"] = False
    else:
        meeting_name = st.text_input("Nom de la réunion", value=st.session_state.get("meeting_name", ""))
    selected_date = st.date_input("Date de la réunion")
    meeting_date = selected_date if isinstance(selected_date, date) else selected_date[0] if selected_date else None
    uploaded_file = st.file_uploader("Déposer le fichier mp3", type=["mp3"])

    if st.button("Ajouter", key="add_meeting"):
        if not meeting_name:
            st.error("Veuillez entrer un nom de réunion")
        elif not meeting_date:
            st.error("Veuillez sélectionner une date")
        elif uploaded_file is None:
            st.error("Veuillez déposer un fichier mp3")
        else:
            with st.spinner("La transcription est en cours, veuillez patienter..."):
                if meeting_id := meeting_service.transcribe_meeting(uploaded_file, meeting_name, meeting_date):
                    # Réinitialiser les champs via rerun
                    st.session_state["tabs"] = Tab.HISTORY.value
                    st.session_state["reset_form"] = True
                    meeting_service.sync_meetings(include_remote=True)
                    st.rerun()

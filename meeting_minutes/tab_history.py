from typing import Dict
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
import pandas as pd
from sqlalchemy.orm import Session

from meeting_minutes.models import Meeting, Prompt
from meeting_minutes.repository import MeetingRepository, PromptRepository, QueryRepository, TranscriptRepository
from meeting_minutes.services import MeetingService, TranscriptionService


def tab_history(db: Session, meeting_service: MeetingService, transcription_service: TranscriptionService):
    """Gestion de l'historique des réunions."""
    col_header, col_refresh = st.columns([0.99, 0.01])
    with col_header:
        st.header("Historique")
    with col_refresh:
        if st.button("🔄", help="Mettre à jour la liste des réunions", key="refresh_meetings"):
            meeting_service.sync_meetings(include_remote=True)
            st.rerun()
    col1, col2 = st.columns([1, 1])
    meeting_id = None
    with col1:
        st.subheader("Meetings")
        meetings: Dict[str, Meeting] = MeetingRepository.get_all(db)
        if meetings:
            # Créer le DataFrame
            df = pd.DataFrame(
                data=[
                    {
                        "ID": meeting.id,
                        "Nom": meeting.name,
                        "Date réunion": str(meeting.date),
                        "Créée": meeting.created,
                        "Statut": meeting.status,
                    }
                    for meeting in meetings.values()
                ],
                columns=["ID", "Nom", "Date réunion", "Créée", "Statut"],
            )

            # Configurer AgGrid
            gb = GridOptionsBuilder.from_dataframe(df)
            # Sort by meeting date in descending order
            gb.configure_default_column(sort_descending_first=True)
            gb.configure_grid_options(defaultColDef={"sortable": True})
            gb.configure_column("Date réunion", sort="desc")
            # Ajuster la largeur des colonnes
            gb.configure_column("ID", minWidth=200)
            gb.configure_column("Nom", minWidth=300)
            gb.configure_selection("single", use_checkbox=False)

            grid_options = gb.build()

            grid_response = AgGrid(
                df,
                gridOptions=grid_options,
                columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
                theme="streamlit",
            )

            # Gérer la sélection et les actions
            selected_rows = grid_response["selected_rows"]
            if selected_rows is not None and not selected_rows.empty:
                meeting_id = selected_rows.iloc[0]["ID"]

                # Section suppression
                with st.popover(f"Supprimer la réunion {meeting_id}"):
                    st.write("Êtes-vous sûr de vouloir supprimer cette réunion ?")
                    if st.button("Confirmer la suppression", key="confirm_delete_meeting"):
                        MeetingRepository.soft_delete(db, meeting_id)
                        TranscriptionService.delete_transcript(meeting_id)
                        st.success("Réunion supprimée avec succès")
                        st.rerun()

                # Section transcript
                transcript = TranscriptRepository.get_transcript(db, meeting_id)
                if transcript:
                    st.text_area("Transcript", value=transcript.transcript, height=150, disabled=True)

                # Récupérer les prompts
                prompts: Dict[int, Prompt] = PromptRepository.get_all(db, include_deleted=False)

                col_but, col_text = st.columns([1, 3])
                with col_but:
                    st.text("Prompts prédéfinis")
                    # Créer les boutons pour chaque prompt
                    for prompt in prompts.values():
                        if st.button(prompt.name, key=f"prompt_btn_{prompt.id}"):
                            st.session_state.selected_prompt = prompt.prompt
                with col_text:
                    # Zone de texte pour la question
                    prompt = st.text_area(
                        "Nouvelle question",
                        value=st.session_state.get("selected_prompt", ""),
                        height=100,
                        key="question_text_area",
                    )

                    if st.button("Envoyer"):
                        with st.spinner("La réponse est en cours de génération, veuillez patienter..."):
                            answer = transcription_service.lemur_task(meeting_id, prompt)
                            if answer:
                                QueryRepository.store_query(db, meeting_id, prompt, answer)
                                st.success("Réponse générée avec succès")
                                st.text_area("Réponse", value=answer, height=400)
            else:
                st.info("Veuillez sélectionner une réunion dans le tableau pour afficher le transcript")
        else:
            st.write("No meetings recorded yet.")
    with col2:
        st.subheader("Questions")
        # Récupérer les queries pour ce meeting
        queries = None
        if meeting_id:
            queries = QueryRepository.get_by_meeting(db, meeting_id)

        if queries:
            # Afficher la liste des questions
            df_queries = pd.DataFrame(
                data=[
                    {
                        "ID": query.id,
                        "Date": query.created,
                        "Question": query.question,
                        "Réponse": query.answer,
                    }
                    for query in queries.values()
                ],
                columns=["ID", "Date", "Question", "Réponse"],
            )

            gb = GridOptionsBuilder.from_dataframe(df_queries)
            gb.configure_selection("single", use_checkbox=False)
            gb.configure_column("Réponse", hide=True)
            gb.configure_default_column(sort_descending_first=True)
            gb.configure_grid_options(defaultColDef={"sortable": True})
            gb.configure_column("Date", sort="asc")

            grid_options_queries = gb.build()

            grid_response_queries = AgGrid(
                df_queries,
                gridOptions=grid_options_queries,
                columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
                theme="streamlit",
                key="queries_table",
            )

            # Gérer la sélection et l'affichage de la réponse
            selected_query_rows = grid_response_queries["selected_rows"]
            if selected_query_rows is not None and not selected_query_rows.empty:
                query_id = int(selected_query_rows.iloc[0]["ID"])
                # Section suppression
                with st.popover(f"Supprimer la question {query_id}"):
                    st.write("Êtes-vous sûr de vouloir supprimer cette question ?")
                    if st.button("Confirmer la suppression", key="confirm_delete_query"):
                        QueryRepository.soft_delete(db, query_id)
                        st.success("Question supprimée avec succès")
                        st.rerun()
                st.text_area("Question", value=selected_query_rows.iloc[0]["Question"], height=100, disabled=True)
                st.text_area("Réponse", value=selected_query_rows.iloc[0]["Réponse"], height=300, disabled=True)
                # Section modification
                with st.expander("Modifier la réponse"):
                    new_answer = st.text_area(
                        "Réponse", value=selected_query_rows.iloc[0]["Réponse"], height=300, key=f"query_{query_id}"
                    )

                    if st.button("Enregistrer la réponse", key=f"save_{query_id}") and (
                        new_answer and new_answer != selected_query_rows.iloc[0]["Réponse"]
                    ):
                        QueryRepository.update_query(db, query_id, answer=new_answer)
                        st.success("Réponse mise à jour avec succès")
                        st.rerun()

        else:
            st.info("Aucune question enregistrée pour cette réunion")

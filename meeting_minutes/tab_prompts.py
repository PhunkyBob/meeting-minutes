import streamlit as st
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
import pandas as pd
from sqlalchemy.orm import Session

from meeting_minutes.repository import PromptRepository


def tab_prompts(db: Session):
    """Gestion des prompts prédéfinis."""
    st.header("Gestion des prompts prédéfinis")

    # Récupérer les prompts existants
    prompts = PromptRepository.get_all(db)

    # Créer le DataFrame
    df_prompts = pd.DataFrame(
        data=[
            {
                "ID": prompt.id,
                "Nom": prompt.name,
                "Prompt": prompt.prompt,
            }
            for prompt in prompts.values()
        ],
        columns=["ID", "Nom", "Prompt"],
    )

    # Configurer AgGrid
    gb_prompts = GridOptionsBuilder.from_dataframe(df_prompts)
    gb_prompts.configure_column("Nom", minWidth=300)
    gb_prompts.configure_column("Prompt", minWidth=400)
    gb_prompts.configure_selection("single", use_checkbox=False)
    grid_options_prompts = gb_prompts.build()

    # Bouton de mise à jour et tableau
    grid_response_prompts = AgGrid(
        df_prompts,
        gridOptions=grid_options_prompts,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        theme="streamlit",
        key="prompts_table",
    )
    if st.button("🔄", help="Mettre à jour la liste des prompts", key="refresh_prompts"):
        st.rerun()

    # Gérer la sélection et les actions
    selected_prompt_rows = grid_response_prompts["selected_rows"]
    if selected_prompt_rows is not None and not selected_prompt_rows.empty:
        prompt_id = int(selected_prompt_rows.iloc[0]["ID"])

        # Section suppression
        with st.popover(f"Supprimer le prompt {selected_prompt_rows.iloc[0]['Nom']}"):
            st.write("Êtes-vous sûr de vouloir supprimer ce prompt ?")
            if st.button("Confirmer la suppression", key=f"delete_{prompt_id}"):
                PromptRepository.soft_delete(db, prompt_id)
                st.success("Prompt supprimé avec succès")
                st.rerun()

        # Section modification
        with st.expander("Modifier le prompt"):
            new_name = st.text_input("Nom", value=selected_prompt_rows.iloc[0]["Nom"], key=f"name_{prompt_id}")
            new_prompt = st.text_area(
                "Prompt", value=selected_prompt_rows.iloc[0]["Prompt"], height=150, key=f"prompt_{prompt_id}"
            )

            if st.button("Enregistrer les modifications", key=f"save_{prompt_id}"):
                if new_name and new_prompt:
                    PromptRepository.update(db, prompt_id, new_name, new_prompt)
                    st.success("Prompt mis à jour avec succès")
                    st.rerun()

    # Ajout d'un nouveau prompt
    with st.expander("Ajouter un nouveau prompt"):
        if "new_prompt_name" not in st.session_state:
            st.session_state.new_prompt_name = ""
        if "new_prompt_text" not in st.session_state:
            st.session_state.new_prompt_text = ""

        new_prompt_name = st.text_input(
            "Nom du nouveau prompt", value=st.session_state.new_prompt_name, key="new_prompt_name_input"
        )
        new_prompt_text = st.text_area(
            "Contenu du prompt", value=st.session_state.new_prompt_text, height=150, key="new_prompt_text_input"
        )

        if st.button("Ajouter le prompt"):
            if new_prompt_name and new_prompt_text:
                PromptRepository.create(db, new_prompt_name, new_prompt_text)
                st.success("Prompt ajouté avec succès")
                st.session_state.new_prompt_name = ""
                st.session_state.new_prompt_text = ""
                st.rerun()
            else:
                st.error("Veuillez remplir tous les champs")

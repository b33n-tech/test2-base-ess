import streamlit as st
import pandas as pd
from supabase import create_client

# --- Connexion Supabase ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]  # service role key
supabase = create_client(url, key)

st.title("🌱 Centralisation des offres ESS")

# --- AJOUTER UNE OFFRE ---
st.subheader("➕ Ajouter une offre")
titre = st.text_input("Nom de l'offre")
url_offre = st.text_input("URL")
date_limite = st.date_input("Date limite")

if st.button("Ajouter"):
    if titre and url_offre and date_limite:
        supabase.table("offres").insert([{
            "titre": titre,
            "url": url_offre,
            "date_limite": date_limite.isoformat(),
            "valide": False,
            "cree_le": pd.Timestamp.now().isoformat()
        }]).execute()
        st.success("Offre ajoutée (en attente de validation)")
    else:
        st.warning("Merci de remplir tous les champs")

# --- ESPACE ADMIN ---
st.subheader("🛠 Admin : Offres en attente")
try:
    response = supabase.table("offres").select("*").order("cree_le").execute()
    df = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"Erreur lecture DB : {e}")
    df = pd.DataFrame()

# Offres non validées
pending = df[df['valide'] == False] if not df.empty else pd.DataFrame()
for idx, row in pending.iterrows():
    st.write(f"{row['titre']} | {row['url']} | {row['date_limite']}")
    col1, col2 = st.columns(2)
    if col1.button(f"Valider {row['id']}"):
        supabase.table("offres").update({"valide": True}).eq("id", row['id']).execute()
        st.experimental_rerun()
    if col2.button(f"Supprimer {row['id']}"):
        supabase.table("offres").delete().eq("id", row['id']).execute()
        st.experimental_rerun()

# --- PARTIE PUBLIQUE ---
st.subheader("📊 Offres publiées")
published = df[df['valide'] == True] if not df.empty else pd.DataFrame()
st.dataframe(published[['titre','url','date_limite']])

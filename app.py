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
date_limite = st.date_input("Date limite")  # optionnel, peut stocker dans une colonne si besoin

if st.button("Ajouter"):
    if titre and url_offre:
        supabase.table("offres").insert([{
            "titre": titre,
            "url": url_offre,
            "valide": False,
            "created_at": pd.Timestamp.now().isoformat()
        }]).execute()
        st.success("Offre ajoutée (en attente de validation)")
    else:
        st.warning("Merci de remplir tous les champs")

# --- ESPACE ADMIN ---
st.subheader("🛠 Admin : Offres en attente")
# Petit mot de passe admin minimal pour le proto
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin123")
pwd = st.text_input("Mot de passe admin", type="password")
admin_logged = False
if st.button("Se connecter admin"):
    if pwd == ADMIN_PASSWORD:
        admin_logged = True
        st.success("Connecté en admin ✅")
    else:
        st.error("Mot de passe incorrect ❌")

# --- Récupérer toutes les offres ---
try:
    response = supabase.table("offres").select("*").order("created_at", {"ascending": False}).execute()
    df = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"Erreur lecture DB : {e}")
    df = pd.DataFrame()

# Admin : filtrer offres non validées
if admin_logged and not df.empty:
    pending = df[df['valide'] == False]
    for idx, row in pending.iterrows():
        st.write(f"{row['titre']} | {row['url']} | créé le {row['created_at']}")
        col1, col2 = st.columns(2)
        if col1.button(f"Valider {row['id']}"):
            supabase.table("offres").update({"valide": True}).eq("id", row['id']).execute()
            st.experimental_rerun()
        if col2.button(f"Supprimer {row['id']}"):
            supabase.table("offres").delete().eq("id", row['id']).execute()
            st.experimental_rerun()

# --- PARTIE PUBLIQUE ---
st.subheader("📊 Offres publiées")
if not df.empty:
    published = df[df['valide'] == True]
    st.dataframe(published[['titre','url','created_at']])
else:
    st.info("Aucune offre pour le moment")

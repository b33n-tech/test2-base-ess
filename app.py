import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

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
        try:
            supabase.table("offres").insert({
                "titre": titre,
                "url": url_offre,
                "valide": False,
                "created_at": datetime.now().isoformat()
            }).execute()
            st.success("Offre ajoutée (en attente de validation)")
        except Exception as e:
            st.error(f"Erreur lors de l'ajout : {e}")
    else:
        st.warning("Merci de remplir tous les champs")

# --- ESPACE ADMIN ---
st.subheader("🛠 Admin : Offres en attente")

# Petit mot de passe admin minimal pour le proto
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin123")

# Utiliser session_state pour persister la connexion admin
if 'admin_logged' not in st.session_state:
    st.session_state.admin_logged = False

pwd = st.text_input("Mot de passe admin", type="password")

if st.button("Se connecter admin"):
    if pwd == ADMIN_PASSWORD:
        st.session_state.admin_logged = True
        st.success("Connecté en admin ✅")
    else:
        st.error("Mot de passe incorrect ❌")

# --- Récupérer toutes les offres ---
try:
    response = supabase.table("offres").select("*").order("created_at", desc=True).execute()
    df = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"Erreur lecture DB : {e}")
    df = pd.DataFrame()

# Admin : filtrer offres non validées
if st.session_state.admin_logged and not df.empty:
    pending = df[df['valide'] == False]
    if not pending.empty:
        for idx, row in pending.iterrows():
            st.write(f"**{row['titre']}** | {row['url']} | créé le {row['created_at']}")
            col1, col2 = st.columns(2)
            if col1.button(f"Valider", key=f"val_{row['id']}"):
                try:
                    supabase.table("offres").update({"valide": True}).eq("id", row['id']).execute()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur validation : {e}")
            if col2.button(f"Supprimer", key=f"del_{row['id']}"):
                try:
                    supabase.table("offres").delete().eq("id", row['id']).execute()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur suppression : {e}")
    else:
        st.info("Aucune offre en attente de validation")

# --- PARTIE PUBLIQUE ---
st.subheader("📊 Offres publiées")
if not df.empty:
    published = df[df['valide'] == True]
    if not published.empty:
        st.dataframe(published[['titre', 'url', 'created_at']], use_container_width=True)
    else:
        st.info("Aucune offre publiée pour le moment")
else:
    st.info("Aucune offre pour le moment")

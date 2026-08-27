import streamlit as st

st.title("HR Insight Copilot")

st.write("Kérdezz a HR-adatokról!")

question = st.text_input(
    "Milyen elemzést szeretnél?",
    placeholder="Például: Melyik területen a legmagasabb a fluktuáció?"
)

if st.button("Elemzés indítása"):
    if question:
        st.success("A kérdésedet megkaptam.")
        st.write(f"Ezt kérdezted: {question}")
    else:
        st.warning("Először írj be egy kérdést.")
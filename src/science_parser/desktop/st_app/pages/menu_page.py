import streamlit as st


_, col_f, col_s, _ = st.columns(4)


with col_f:
    if st.button("Получить публикации по ISSN журнала"):
        st.switch_page("pages/agregators_page.py")

with col_s:
    if st.button("AI парсер"):
        st.switch_page("pages/ai_parser_page.py")

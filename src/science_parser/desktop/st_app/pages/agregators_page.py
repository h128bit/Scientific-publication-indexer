from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st

from science_parser.desktop.st_app.utils.article_loader import ArticleLoader 


# FUNCTIONS

def file_dialog():
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    # Открываем диалог выбора папки
    folder = filedialog.askdirectory(
        title="Выберите папку для сохранения",
        initialdir=st.session_state.save_path
    )
    
    root.destroy()
    return folder


# SETUPS 

article_loader = ArticleLoader()


# SESSIONS SETTINGS

if "save_path" not in st.session_state:
    st.session_state.save_path = str(Path.home() / "Downloads")


# INTERFACE

if st.button(":material/home: Домой"):
    st.switch_page("pages/menu_page.py")

st.write("### Crossref")

col = st.columns(1)[0]

with col:
    dfirst, dsecond, issncol = st.columns(3)
    now_date = datetime.now()

    with dfirst:
        date_from = st.date_input("Начало периода :material/calendar_month:", now_date - timedelta(days=7), format="DD.MM.YYYY")
        date_from = date_from.strftime('%Y-%m-%d')

    with dsecond:
        date_to = st.date_input("Конец периода :material/calendar_month:", now_date, format="DD.MM.YYYY")
        date_to = date_to.strftime('%Y-%m-%d')

    with issncol:
        electronic_issn = st.text_input("ISSN", validate=(r"^[0-9]{4}-[0-9]{3}[0-9Xx]$", "issn должен быть в формате `1234-1234` или `1234-123x`")).lower()

c1, c2 = st.columns(2)
with c1:
    if st.button("Выбрать папку для сохранения документов"):
        folder = file_dialog()
        if folder:
            st.session_state.save_path = folder
            st.rerun() 
with c2:
    st.code(st.session_state.save_path, language=None)

if st.button("Выгрузить"):
    counter = 0
    loader = article_loader.download_by_issn(date_from=date_from, 
                                            date_to=date_to, 
                                            issn=electronic_issn, 
                                            path_to_save=st.session_state.save_path)
    try:

        with st.status("Скачивание файлов...", expanded=False, type="compact") as status:
            for item_state in loader:
                counter += 1
                status.update(label=f"Скачивание файлов... Страница: {item_state["page_num"]}.  {item_state["item"]}/{item_state["page_size"]}", 
                              state="running")
            status.update(label=f"Завершено! скачено файлов: {counter}", state="complete")

    except Exception as e:
        st.json(article_loader.status)


    download_status = article_loader.get_report()

    date_first = None 
    date_second = None
    if download_status["date_from"]:
        date_first = download_status["date_from"].strftime("%d.%m.%Y")
    if download_status["date_to"]:
        date_second = download_status["date_to"].strftime("%d.%m.%Y")

    st.table(
        {
            ":material/folder: Получено метаданных": str(download_status["number_articles"]),
            ":material/expand_circle_down: Статей с Open Access": str(download_status["with_oa_num"]),
            ":material/date_range: Диапазон дат": f"{date_first} - {date_second}"
        },
        border="horizontal",
        width="content",
    )
import os
import json
from pathlib import Path

import streamlit as st
from pandas import DataFrame

from science_parser.core.licenses.manager import LICENSE_FILE_PATH

# FUNCTIONS

def file_dialog():
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    # Открываем диалог выбора папки
    file_path = filedialog.askopenfilename(
        title="Выберите файл лицензий",
        initialdir=Path.cwd(),
        filetypes=(("Json файлы", "*.json"), ("Все файлы", "*.*"))
    )
    
    root.destroy()
    return file_path


def validate_license_file(path: Path):

    try:
        with open(path, "r", encoding="utf-8") as f:
            s = f.read()
    except Exception as e:
        return False, "Не удалось открыть файл"

    try:
        ll = json.loads(s)
    except Exception as e:
        return False, "Некорректный JSON"

    if not isinstance(ll, (list, tuple)):
        return False, "Файл должен содержать только список лицензий"

    if len(ll) == 0:
        return False, "Список лицензий пустой"

    return True, "ok"

    


# DIALOG FUNCTIONS

@st.dialog("Лицензий")
def license_settings():
    st.write("Экспорт лицензий")
    with open(LICENSE_FILE_PATH, "rb") as f:
        file = f.read()
    st.download_button(label="Экспорт", data=file, file_name="licenses.json", mime="application/json")

    use_build_in = st.checkbox("Использовать встроенные лицензии", value=True)

    if not use_build_in:
        st.write("Импорт лицензий") 
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Открыть..."):
                file_path = Path(file_dialog())

                status, msg = validate_license_file(file_path)
                with col2:
                    if status:
                        st.success("Успешно!")
                        os.environ["SCIPARSER_LICENSES_FILE"] = str(file_path)
                    else: 
                        st.error(msg)
    if st.button("Готово"):
        st.rerun()


@st.dialog("Конфигурация LLM")
def llm_settings():
    df = DataFrame(
        [
            {"Endpoint": "http://127.0.0.1:8000/v1", "Название модели": "Model name", "API токен": "your-api-key-here"}
        ]
    )
    edited_df = st.data_editor(df)

    st.write(edited_df)

    if st.button("Готово"):
        st.rerun()


#  INTERFACE


st.markdown("# Индексатор научных публикаций\n#### Лаунчер")

if st.button("Запустить :material/play_circle:"):
    st.switch_page("pages/menu_page.py")


_, col_f, col_s, _ = st.columns(4)


with col_f:
    if st.button("Настроить лицензии"):
        license_settings()

with col_s:
    if st.button("Настроить LLM"):
        llm_settings()

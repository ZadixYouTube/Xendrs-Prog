import streamlit as st
import sqlite3
import hashlib
import uuid
import random

st.set_page_config(page_title="PaLexis Ultimate", page_icon="💜", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1621 !important; color: #ffffff; }
    .stChatInputContainer iframe { background-color: #17212b !important; }
    .stChatMessage {
        background-color: #182533 !important;
        border-radius: 12px !important;
        padding: 10px !important;
        margin-bottom: 10px !important;
    }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    
    div.stButton > button {
        background-color: transparent !important;
        color: #708599 !important;
        border: none !important;
        font-size: 20px !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        transition: color 0.3s ease;
    }
    div.stButton > button:hover { color: #5288c1 !important; background-color: transparent !important; }
    div.stButton > button:disabled {
        color: #5288c1 !important;
        border-bottom: 3px solid #5288c1 !important;
        border-radius: 0px !important;
        background-color: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

conn = sqlite3.connect("messenger.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    uid TEXT PRIMARY KEY, username TEXT, password TEXT, avatar BLOB
)""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS chats (
    chat_id TEXT PRIMARY KEY, chat_name TEXT, is_channel INTEGER, creator_uid TEXT
)""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT, user_uid TEXT, 
    username TEXT, text TEXT, media BLOB, media_type TEXT
)""")
conn.commit()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_uid = None
    st.session_state.username = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Чаты"
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

def set_tab(tab_name):
    st.session_state.active_tab = tab_name

col_logo, col_t1, col_t2, col_t3, col_t4, _ = st.columns([2, 1.5, 1.5, 1.5, 1.5, 4.5])
with col_logo:
    st.markdown("<h2 style='margin:0; color:#5288c1; font-weight:700;'>PaLexis-(0.1)</h2>", unsafe_allow_html=True)

if st.session_state.logged_in:
    with col_t1: st.button("Чаты", key="t_chats", disabled=(st.session_state.active_tab == "Чаты"), on_click=set_tab, args=("Чаты",))
    with col_t2: st.button("Друзья", key="t_friends", disabled=(st.session_state.active_tab == "Друзья"), on_click=set_tab, args=("Друзья",))
    with col_t3: st.button("Группы / Каналы", key="t_chans", disabled=(st.session_state.active_tab == "Каналы"), on_click=set_tab, args=("Каналы",))
    with col_t4: st.button("Профиль", key="t_prof", disabled=(st.session_state.active_tab == "Профиль"), on_click=set_tab, args=("Профиль",))
else:
    with col_t1: st.button("Вход / Регистрация", disabled=True)

st.write("---")

if not st.session_state.logged_in:
    st.subheader("🔐 Добро пожаловать в PaLexis-Chat!")
    menu = ["Вход", "Регистрация"]
    choice = st.radio("Выберите действие:", menu, horizontal=True)
    
    login_user = st.text_input("Логин (Имя пользователя):")
    login_pass = st.text_input("Пароль:", type="password")
    
    if choice == "Регистрация":
        if st.button("Создать аккаунт", use_container_width=True):
            cursor.execute("SELECT * FROM users WHERE username = ?", (login_user,))
            if cursor.fetchone():
                st.error("Пользователь с таким именем уже существует!")
            elif login_user and login_pass:
                new_uid = f"ID-{random.randint(100000, 999999)}"
                hashed_pass = hashlib.sha256(login_pass.encode()).hexdigest()
                cursor.execute("INSERT INTO users (uid, username, password, avatar) VALUES (?, ?, ?, NULL)", (new_uid, login_user, hashed_pass))
                conn.commit()
                st.success(f"Регистрация успешна! Ваш уникальный {new_uid}. Теперь войдите.")
    
    elif choice == "Вход":
        if st.button("Войти", use_container_width=True):
            hashed_pass = hashlib.sha256(login_pass.encode()).hexdigest()
            cursor.execute("SELECT uid, username FROM users WHERE username = ? AND password = ?", (login_user, hashed_pass))
            user = cursor.fetchone()
            if user:
                st.session_state.logged_in = True
                st.session_state.user_uid = user[0]
                st.session_state.username = user[1]
                st.rerun()
            else:
                st.error("Неверное имя пользователя или пароль!")
    st.stop()

if st.session_state.active_tab == "Чаты":
    col_left, col_right = st.columns([1, 3])
    
    with col_left:
        st.markdown("### 📌 Список чатов")
        cursor.execute("SELECT chat_id, chat_name, is_channel FROM chats")
        all_chats = cursor.fetchall()
        
        if not all_chats:
            st.info("У вас пусто. Создайте или найдите чат в меню сверху!")
        else:
            for ch_id, ch_name, is_chan in all_chats:
                if is_chan == 1: icon = "👥"
                elif is_chan == 2: icon = "📢"
                else: icon = "💬"
                
                c_name, c_d = st.columns([8, 2])
                with c_name:
                    if st.button(f"{icon} {ch_name}", key=f"ch_{ch_id}", disabled=(ch_id == st.session_state.current_chat), use_container_width=True):
                        st.session_state.current_chat = ch_id
                        st.rerun()
                with c_d:
                    if st.button("🗑️", key=f"del_{ch_id}"):
                        cursor.execute("DELETE FROM chats WHERE chat_id = ?", (ch_id,))
                        cursor.execute("DELETE FROM messages WHERE chat_id = ?", (ch_id,))
                        conn.commit()
                        st.session_state.current_chat = None
                        st.rerun()

    with col_right:
        if st.session_state.current_chat:
            ch_id = st.session_state.current_chat
            cursor.execute("SELECT chat_name, is_channel, creator_uid FROM chats WHERE chat_id = ?", (ch_id,))
            ch_info = cursor.fetchone()
            
            ch_title, is_chan, creator_uid = ch_info[0], ch_info[1], ch_info[2]
            type_label = "👥 Группа" if is_chan == 1 else ("📢 Канал" if is_chan == 2 else "💬 Диалог")
            st.markdown(f"### {type_label}: {ch_title}")
            
            cursor.execute("SELECT user_uid, username, text, media, media_type FROM messages WHERE chat_id = ? ORDER BY id ASC", (ch_id,))
            for u_uid, u_name, text, media, m_type in cursor.fetchall():
                cursor.execute("SELECT avatar FROM users WHERE uid = ?", (u_uid,))
                av_blob = cursor.fetchone()[0]
                avatar_to_show = av_blob if av_blob else "😎"
                
                with st.chat_message("user", avatar=avatar_to_show):
                    st.write(f"{u_name} <span style='color:#708599; font-size:12px;'>({u_uid})</span>", unsafe_allow_html=True)
                    if text: st.write(text)
                    if media:
                        if m_type.startswith("image"): st.image(media, width=400)
                        elif m_type.startswith("video"): st.video(media)
            
            if is_chan == 2 and st.session_state.user_uid != creator_uid:
                st.warning("🔒 Это канал. Здесь могут писать только администраторы.")
            else:
                col_inp, col_file = st.columns([3, 1])
                with col_inp:
                    prompt = st.chat_input("Напишите сообщение...")
                with col_file:
                    uploaded_file = st.file_uploader("Прикрепить фото/видео", type=["png", "jpg", "jpeg", "mp4", "mov", "mkv"], label_visibility="collapsed")
                
                if prompt or uploaded_file:
                    file_bytes = None
                    file_type = ""
                    if uploaded_file:
                        file_bytes = uploaded_file.read()
                        file_type = uploaded_file.type
                    
                    cursor.execute("INSERT INTO messages (chat_id, user_uid, username, text, media, media_type) VALUES (?, ?, ?, ?, ?, ?)",
                                   (ch_id, st.session_state.user_uid, st.session_state.username, prompt, file_bytes, file_type))
                    conn.commit()
                    st.rerun()
        else:
            st.markdown("<h4 style='text-align: center; color: #708599; margin-top: 50px;'>Выберите диалог, группу или канал слева</h4>", unsafe_allow_html=True)

elif st.session_state.active_tab == "Друзья":
    st.markdown("### 👥 Личные диалоги по ID")
    col_f1, col_f2 = st.columns([3, 1])
    with col_f1: friend_id = st.text_input("Введите ID друга для создания чата:")
    with col_f2:
        st.write("##")
        if st.button("Начать чат", use_container_width=True):
            if friend_id:
                cursor.execute("SELECT username FROM users WHERE uid = ?", (friend_id,))
                f_exist = cursor.fetchone()
                if f_exist:
                    chat_id = f"p2p_{min(st.session_state.user_uid, friend_id)}_{max(st.session_state.user_uid, friend_id)}"
                    cursor.execute("INSERT OR IGNORE INTO chats (chat_id, chat_name, is_channel, creator_uid) VALUES (?, ?, 0, NULL)", (chat_id, f"Чат с {f_exist[0]}"))
                    conn.commit()
                    st.session_state.current_chat = chat_id
                    st.session_state.active_tab = "Чаты"
                    st.rerun()
                else:
                    st.error("Пользователь с таким ID не найден.")

elif st.session_state.active_tab == "Каналы":
    st.markdown("### 📢 Управление группами и каналами")
    
    col_c1, col_c2, col_c3 = st.columns([3, 1, 1])
    with col_c1: 
        c_name = st.text_input("Название:")
    with col_c2:
        type_choice = st.radio("Тип сообщества:", ["👥 Группа", "📢 Канал"])
    with col_c3:
        st.write("##")
        if st.button("Создать", use_container_width=True):
            if c_name:
                ch_id = f"pub_{uuid.uuid4().hex[:8]}"
                is_chan_type = 1 if "Группа" in type_choice else 2
                cursor.execute("INSERT INTO chats (chat_id, chat_name, is_channel, creator_uid) VALUES (?, ?, ?, ?)", 
                               (ch_id, c_name, is_chan_type, st.session_state.user_uid))
                conn.commit()
                st.success(f"Успешно создано!")
                st.rerun()
                st.write("---")
    
    st.markdown("### 🔍 Глобальный поиск")
    search_query = st.text_input("Введите название группы или канала для поиска:")
    
    if search_query:
        cursor.execute("SELECT chat_id, chat_name, is_channel FROM chats WHERE chat_name LIKE ? AND is_channel IN (1, 2)", (f"%{search_query}%",))
        search_results = cursor.fetchall()
        
        if search_results:
            for ch_id, ch_name, is_chan_type in search_results:
                icon = "👥 Группа" if is_chan_type == 1 else "📢 Канал"
                col_res_name, col_res_act = st.columns([4, 1])
                with col_res_name:
                    st.markdown(f"{icon} {ch_name}")
                with col_res_act:
                    if st.button("Войти / Посмотреть", key=f"search_{ch_id}"):
                        st.session_state.current_chat = ch_id
                        st.session_state.active_tab = "Чаты"
                        st.rerun()
        else:
            st.warning("Ничего не найдено.")

elif st.session_state.active_tab == "Профиль":
    st.markdown("### 👤 Настройки профиля")
    st.info(f"🧬 Ваш постоянный ID для друзей: {st.session_state.user_uid}")
    
    cursor.execute("SELECT avatar FROM users WHERE uid = ?", (st.session_state.user_uid,))
    current_avatar = cursor.fetchone()[0]
    
    if current_avatar:
        st.image(current_avatar, width=100, caption="Ваша текущая аватарка")
        
    uploaded_avatar = st.file_uploader("Загрузить собственную картинку на аватарку:", type=["jpg", "png", "jpeg"])
    
    if st.button("Сохранить изменения в профиле", use_container_width=True):
        if uploaded_avatar:
            avatar_bytes = uploaded_avatar.read()
            cursor.execute("UPDATE users SET avatar = ? WHERE uid = ?", (avatar_bytes, st.session_state.user_uid))
            conn.commit()
            st.success("Аватарка успешно обновлена!")
            st.rerun()
            
    if st.button("Выйти из аккаунта"):
        st.session_state.logged_in = False
        st.session_state.user_uid = None
        st.rerun()
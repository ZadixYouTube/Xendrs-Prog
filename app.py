import streamlit as st
import psycopg2
import psycopg2.extras
import hashlib
import uuid
import random
import time
from streamlit_cookies_controller import CookieController

DB_URL = "postgresql://neondb_owner:npg_ywHr6FhD3keR@ep-winter-surf-ab4vv5c5.eu-west-2.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    return conn

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    uid TEXT PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    nickname TEXT,
    balance REAL DEFAULT 0.0,
    device_token TEXT,
    avatar BYTEA
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS chats (
    chat_id TEXT PRIMARY KEY,
    chat_name TEXT,
    is_channel INTEGER DEFAULT 0,
    creator_uid TEXT,
    p2p_user1 TEXT,
    p2p_user2 TEXT,
    p2p_name1 TEXT,
    p2p_name2 TEXT
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    chat_id TEXT,
    user_uid TEXT,
    username TEXT,
    text TEXT,
    media BYTEA,
    media_type TEXT,
    timestamp DOUBLE PRECISION
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_friends (
    user_uid TEXT, 
    friend_uid TEXT, 
    PRIMARY KEY (user_uid, friend_uid)
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS group_members (
    chat_id TEXT,
    user_uid TEXT,
    PRIMARY KEY (chat_id, user_uid)
)""")

st.set_page_config(page_title="PaLexis-Chat", page_icon="💜", layout="wide")

controller = CookieController()

st.markdown("""
<style>
    /* Мягкий неяркий тёмный градиент на фон всего приложения */
    .stApp, html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { 
        background: linear-gradient(135deg, #0f111a 0%, #151926 50%, #1a192e 100%) !important; 
        color: #ffffff !important; 
    }
    
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    /* Текст во всем приложении */
    h1, h2, h3, h4, h5, h6, p, span, label, div, small { 
        color: #e2e8f0 !important; 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Поле ввода сообщения (эффект стекла) */
    .stChatInputContainer iframe { background-color: rgba(30, 41, 59, 0.7) !important; }
    .stChatInput textarea { 
        color: #ffffff !important; 
        background-color: rgba(30, 41, 59, 0.7) !important;
        border-radius: 12px !important;
    }
    
    /* Сообщения в чате: сглаженные углы и легкое свечение */
    .stChatMessage {
        background-color: rgba(30, 41, 59, 0.5) !important;
        border-radius: 16px !important;
        padding: 12px 16px !important;
        margin-bottom: 12px !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* Боковое меню (скрываем) */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    
    /* Верхние кнопки табов меню */
    div.stButton > button {
        background-color: rgba(255, 255, 255, 0.03) !important;
        color: #94a3b8 !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    div.stButton > button:hover { 
        color: #8b5cf6 !important; 
        background-color: rgba(139, 92, 246, 0.1) !important;
        border-color: rgba(139, 92, 246, 0.3) !important;
        transform: translateY(-1px);
    }
    div.stButton > button:disabled {
        color: #ffffff !important;
        background: linear-gradient(90deg, #6d28d9 0%, #4c1d95 100%) !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(109, 40, 217, 0.3);
        opacity: 1 !important;
    }
    
    /* Поля ввода (Инпуты) */
    input, [data-testid="stTextInput"] div[data-baseweb="input"], [data-testid="stFileUploader"] {
        background-color: rgba(15, 23, 42, 0.6) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 4px 8px;
    }
    input:focus {
        border-color: #8b5cf6 !important;
    }
    
    /* Всплывающие поповеры */
    [data-testid="stPopoverBody"] {
        background-color: #151926 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
    }
</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_uid = None
    st.session_state.username = None
    st.session_state.nickname = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Чаты"
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

if not st.session_state.logged_in:
    saved_token = controller.get("device_token")
    if saved_token:
        cursor.execute("SELECT uid, username, nickname FROM users WHERE device_token = %s", (saved_token,))
        user = cursor.fetchone()
        if user:
            st.session_state.logged_in = True
            st.session_state.user_uid = user[0]
            st.session_state.username = user[1]
            st.session_state.nickname = user[2] if user[2] else user[1]

def set_tab(tab_name):
    st.session_state.active_tab = tab_name

col_logo, col_t1, col_t2, col_t3, col_t4, _ = st.columns([2, 1.5, 1.5, 1.5, 1.5, 4.5])
with col_logo:
    st.markdown("<h2 style='margin:0; background: linear-gradient(90deg, #a78bfa, #60a5fa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight:800;'>PaLexis Chat 0.2.4</h2>", unsafe_allow_html=True)

if st.session_state.logged_in:
    with col_t1: st.button("💬 Чаты", key="t_chats", disabled=(st.session_state.active_tab == "Чаты"), on_click=set_tab, args=("Чаты",))
    with col_t2: st.button("👥 Друзья", key="t_friends", disabled=(st.session_state.active_tab == "Друзья"), on_click=set_tab, args=("Друзья",))
    with col_t3: st.button("📢 Группы / Каналы", key="t_chans", disabled=(st.session_state.active_tab == "Каналы"), on_click=set_tab, args=("Каналы",))
    with col_t4: st.button("⚙️ Профиль", key="t_prof", disabled=(st.session_state.active_tab == "Профиль"), on_click=set_tab, args=("Профиль",))
else:
    with col_t1: st.button("🔑 Вход / Регистрация", disabled=True)

st.write("---")

if not st.session_state.logged_in:
    st.subheader("🔐 Добро пожаловать в мессенджер")
    menu = ["Вход", "Регистрация"]
    choice = st.radio("Выберите действие:", menu, horizontal=True)
    
    login_user = st.text_input("Логин (Имя пользователя):")
    login_pass = st.text_input("Пароль:", type="password")
    
    if choice == "Регистрация":
        if st.button("Создать аккаунт", use_container_width=True):
            cursor.execute("SELECT * FROM users WHERE username = %s", (login_user,))
            if cursor.fetchone():
                st.error("Пользователь с таким именем уже существует!")
            elif login_user and login_pass:
                new_uid = str(random.randint(100000, 999999))
                while True:
                    cursor.execute("SELECT uid FROM users WHERE uid = %s", (new_uid,))
                    if not cursor.fetchone(): break
                    new_uid = str(random.randint(100000, 999999))
                
                hashed_pass = hashlib.sha256(login_pass.encode()).hexdigest()
                dev_token = str(uuid.uuid4())
                cursor.execute("INSERT INTO users (uid, username, password, avatar, device_token, nickname) VALUES (%s, %s, %s, NULL, %s, %s)", 
                               (new_uid, login_user, hashed_pass, dev_token, login_user))
                conn.commit()
                controller.set("device_token", dev_token)
                st.success(f"Регистрация успешна! Ваш цифровой ID: {new_uid}. Переключитесь на Вход.")
    
    elif choice == "Вход":
        if st.button("Войти", use_container_width=True):
            hashed_pass = hashlib.sha256(login_pass.encode()).hexdigest()
            cursor.execute("SELECT uid, username, device_token, nickname FROM users WHERE username = %s AND password = %s", (login_user, hashed_pass))
            user = cursor.fetchone()
            if user:
                st.session_state.logged_in = True
                st.session_state.user_uid = user[0]
                st.session_state.username = user[1]
                st.session_state.nickname = user[3] if user[3] else user[1]
                
                dev_token = user[2] if user[2] else str(uuid.uuid4())
                cursor.execute("UPDATE users SET device_token = %s WHERE uid = %s", (dev_token, user[0]))
                conn.commit()
                controller.set("device_token", dev_token)
                st.rerun()
            else:
                st.error("Неверное имя пользователя или пароль")
    st.stop()

@st.fragment(run_every=2)
def auto_refresh_listener():
    cursor.execute("SELECT COUNT(*) FROM messages")
    current_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM chats")
    current_chats_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM group_members")
    current_members_count = cursor.fetchone()[0]
    
    if "last_msg_count" not in st.session_state: st.session_state.last_msg_count = current_count
    if "last_chats_count" not in st.session_state: st.session_state.last_chats_count = current_chats_count
    if "last_members_count" not in st.session_state: st.session_state.last_members_count = current_members_count

    if (current_count != st.session_state.last_msg_count or
        current_chats_count != st.session_state.last_chats_count or 
        current_members_count != st.session_state.last_members_count):
        st.session_state.last_msg_count = current_count
        st.session_state.last_chats_count = current_chats_count
        st.session_state.last_members_count = current_members_count
        st.rerun()

auto_refresh_listener()

if st.session_state.active_tab == "Чаты":
    col_left, col_right = st.columns([1, 3])
    
    with col_left:
        st.markdown("### 📌 Список чатов")
        
        cursor.execute("""
            SELECT DISTINCT c.chat_id, c.chat_name, c.is_channel, c.p2p_user1, c.p2p_user2, c.p2p_name1, c.p2p_name2 
            FROM chats c
            LEFT JOIN group_members gm ON c.chat_id = gm.chat_id
            WHERE c.is_channel = 2 
               OR (c.is_channel = 0 AND (c.p2p_user1 = %s OR c.p2p_user2 = %s))
               OR (c.is_channel = 1 AND (c.creator_uid = %s OR gm.user_uid = %s))
        """, (st.session_state.user_uid, st.session_state.user_uid, st.session_state.user_uid, st.session_state.user_uid))
        all_chats = cursor.fetchall()
        
        if not all_chats:
            st.info("У вас пусто. Создайте или найдите чат в меню сверху!")
        else:
            for ch_id, ch_name, is_chan, u1, u2, n1, n2 in all_chats:
                display_name = ch_name
                if is_chan == 0:
                    if st.session_state.user_uid == u1:
                        display_name = n1 if n1 else ch_name
                    else:
                        display_name = n2 if n2 else ch_name
                
                icon = "👥" if is_chan == 1 else ("📢" if is_chan == 2 else "💬")
                
                c_name, c_d = st.columns([8, 2])
                with c_name:
                    if st.button(f"{icon} {display_name}", key=f"ch_{ch_id}", disabled=(ch_id == st.session_state.current_chat), use_container_width=True):
                        st.session_state.current_chat = ch_id
                        st.rerun()
                with c_d:
                    if st.button("🗑", key=f"del_{ch_id}"):
                        cursor.execute("DELETE FROM chats WHERE chat_id = %s", (ch_id,))
                        cursor.execute("DELETE FROM messages WHERE chat_id = %s", (ch_id,))
                        cursor.execute("DELETE FROM group_members WHERE chat_id = %s", (ch_id,))
                        conn.commit()
                        st.session_state.current_chat = None
                        st.rerun()

    with col_right:
        if st.session_state.current_chat:
            ch_id = st.session_state.current_chat
            cursor.execute("SELECT chat_name, is_channel, creator_uid, p2p_user1, p2p_user2, p2p_name1, p2p_name2 FROM chats WHERE chat_id = %s", (ch_id,))
            ch_info = cursor.fetchone()
            
            if ch_info:
                ch_title, is_chan, creator_uid, u1, u2, n1, n2 = ch_info
                display_name = ch_title
                if is_chan == 0:
                    display_name = n1 if st.session_state.user_uid == u1 else n2
                
                type_label = "👥 Приватная Группа" if is_chan == 1 else ("📢 Канал" if is_chan == 2 else "💬 Личный диалог")
                
                col_title_text, col_actions = st.columns([2, 2])
                with col_title_text:
                    st.markdown(f"### {type_label}: {display_name}")
                
                with col_actions:
                    if is_chan == 0:
                        with st.popover("✏️ Изменить название чата"):
                            new_chat_title = st.text_input("Новое название чата:", value=display_name)
                            if st.button("Сохранить название", key=f"save_title_{ch_id}"):
                                if st.session_state.user_uid == u1:
                                    cursor.execute("UPDATE chats SET p2p_name1 = %s WHERE chat_id = %s", (new_chat_title, ch_id))
                                else:
                                    cursor.execute("UPDATE chats SET p2p_name2 = %s WHERE chat_id = %s", (new_chat_title, ch_id))
                                conn.commit()
                                st.rerun()
                    
                    elif is_chan == 1 and st.session_state.user_uid == creator_uid:
                        with st.popover("➕ Добавить участника"):
                            invite_id = st.text_input("Введите цифровой ID пользователя:").replace("ID-", "").strip()
                            if st.button("Добавить в группу", key=f"inv_{ch_id}"):
                                cursor.execute("SELECT username FROM users WHERE uid = %s", (invite_id,))
                                if cursor.fetchone():
                                    cursor.execute("INSERT OR IGNORE INTO group_members (chat_id, user_uid) VALUES (%s, %s)", (ch_id, invite_id))
                                    conn.commit()
                                    st.success("Пользователь добавлен!")
                                else:
                                    st.error("Пользователь c таким ID не существует.")

                cursor.execute("SELECT user_uid, username, text, media, media_type FROM messages WHERE chat_id = %s ORDER BY id ASC", (ch_id,))
                for u_uid, u_name, text, media, m_type in cursor.fetchall():
                    cursor.execute("SELECT avatar, nickname FROM users WHERE uid = %s", (u_uid,))
                    u_data = cursor.fetchone()
                    av_blob = u_data[0] if u_data else None
                    display_author_name = u_data[1] if (u_data and u_data[1]) else u_name
                    avatar_to_show = av_blob if av_blob else "😎"
                    
                    with st.chat_message("user", avatar=avatar_to_show):
                        st.write(f"{display_author_name} <span style='color:#708599; font-size:12px;'>({u_uid})</span>", unsafe_allow_html=True)
                        if text: st.write(text)
                        if media:
                            if m_type.startswith("image"): st.image(bytes(media), width=400)
                            elif m_type.startswith("video"): st.video(bytes(media))
                
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
                        
                        cursor.execute("INSERT INTO messages (chat_id, user_uid, username, text, media, media_type, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                       (ch_id, st.session_state.user_uid, st.session_state.nickname, prompt, file_bytes, file_type, time.time()))
                        conn.commit()
                        st.rerun()
            else:
                st.session_state.current_chat = None
        else:
            st.markdown("<h4 style='text-align: center; color: #708599; margin-top: 50px;'>Выберите диалог, группу или канал слева</h4>", unsafe_allow_html=True)

elif st.session_state.active_tab == "Друзья":
    st.markdown("### 👥 Список ваших друзей")
    
    col_f1, col_f2 = st.columns([3, 1])
    with col_f1: 
        friend_input = st.text_input("Введите цифровой ID пользователя, чтобы добавить в друзья:")
    with col_f2:
        st.write("##")
        if st.button("Добавить в список", use_container_width=True):
            if friend_input:
                friend_id = friend_input.replace("ID-", "").strip()
                
                if friend_id == st.session_state.user_uid:
                    st.error("Нельзя добавить в друзья самого себя!")
                else:
                    cursor.execute("SELECT username FROM users WHERE uid = %s", (friend_id,))
                    if cursor.fetchone():
                        cursor.execute("INSERT INTO user_friends (user_uid, friend_uid) VALUES (%s, %s) ON CONFLICT DO NOTHING", 
                                       (st.session_state.user_uid, friend_id))
                        conn.commit()
                        st.success("Пользователь успешно добавлен в друзья!")
                        st.rerun()
                    else:
                        st.error("Пользователь с таким цифровым ID не найден.")

    st.write("---")
    st.markdown("### 📇 Мои контакты")
    
    cursor.execute("""
        SELECT u.uid, u.nickname, u.username 
        FROM user_friends f
        JOIN users u ON f.friend_uid = u.uid
        WHERE f.user_uid = %s
    """, (st.session_state.user_uid,))
    friends_list = cursor.fetchall()
    
    if friends_list:
        for f_id, f_nick, f_login in friends_list:
            display_name = f_nick if f_nick else f_login
            
            col_friend_info, col_friend_chat, col_friend_del = st.columns([5, 2, 1])
            
            with col_friend_info:
                st.markdown(f"😎 **{display_name}** `(ID: {f_id})`")
                
            with col_friend_chat:
                if st.button(f"💬 Начать чат", key=f"chat_with_{f_id}", use_container_width=True):
                    chat_id = f"p2p_{min(st.session_state.user_uid, f_id)}_{max(st.session_state.user_uid, f_id)}"
                    
                    cursor.execute("""
                        INSERT INTO chats 
                        (chat_id, chat_name, is_channel, creator_uid, p2p_user1, p2p_user2, p2p_name1, p2p_name2) 
                        VALUES (%s, %s, 0, NULL, %s, %s, %s, %s) ON CONFLICT DO NOTHING
                    """, (chat_id, f"Чат с {display_name}", st.session_state.user_uid, f_id, f"Чат с {display_name}", f"Чат с {st.session_state.nickname}"))
                    conn.commit()
                    
                    st.session_state.current_chat = chat_id
                    st.session_state.active_tab = "Чаты"
                    st.rerun()
                    
            with col_friend_del:
                if st.button("🗑", key=f"rem_fr_{f_id}", use_container_width=True):
                    cursor.execute("DELETE FROM user_friends WHERE user_uid = %s AND friend_uid = %s", 
                                   (st.session_state.user_uid, f_id))
                    conn.commit()
                    st.rerun()
    else:
        st.info("Ваш список друзей пока пуст.")

elif st.session_state.active_tab == "Каналы":
    st.markdown("### 📢 Управление группами и каналами")
    col_c1, col_c2, col_c3 = st.columns([3, 1, 1])
    with col_c1: c_name = st.text_input("Название:")
    with col_c2: type_choice = st.radio("Тип сообщества:", ["👥 Группа (Приватная)", "📢 Канал (Публичный)"])
    with col_c3:
        st.write("##")
        if st.button("Создать", use_container_width=True):
            if c_name:
                ch_id = f"pub_{uuid.uuid4().hex[:8]}"
                is_chan_type = 1 if "Группа" in type_choice else 2
                cursor.execute("INSERT INTO chats (chat_id, chat_name, is_channel, creator_uid) VALUES (%s, %s, %s, %s)", 
                               (ch_id, c_name, is_chan_type, st.session_state.user_uid))
                conn.commit()
                st.success(f"Успешно создано!")
                st.rerun()
                
    st.write("---")
    st.markdown("### 🔍 Глобальный поиск каналов")
    search_query = st.text_input("Введите название канала для поиска (Группы скрыты из поиска):")
    if search_query:
        cursor.execute("SELECT chat_id, chat_name, is_channel FROM chats WHERE chat_name ILIKE %s AND is_channel = 2", (f"%{search_query}%",))
        search_results = cursor.fetchall()
        if search_results:
            for ch_id, ch_name, is_chan_type in search_results:
                icon = "📢 Канал"
                col_res_name, col_res_act = st.columns([4, 1])
                with col_res_name: st.markdown(f"{icon} {ch_name}")
                with col_res_act:
                    if st.button("Войти / Посмотреть", key=f"search_{ch_id}"):
                        st.session_state.current_chat = ch_id
                        st.session_state.active_tab = "Чаты"
                        st.rerun()
        else:
            st.warning("Ничего не найдено.")

elif st.session_state.active_tab == "Профиль":
    st.markdown("### 👤 Настройки профиля")
    st.info(f"🧬 Ваш постоянный цифровой ID для друзей: {st.session_state.user_uid}")
    
    cursor.execute("SELECT avatar, nickname FROM users WHERE uid = %s", (st.session_state.user_uid,))
    u_db_data = cursor.fetchone()
    current_avatar = u_db_data[0] if u_db_data else None
    current_nickname = u_db_data[1] if (u_db_data and u_db_data[1]) else st.session_state.username
    
    if current_avatar:
        st.image(bytes(current_avatar), width=100, caption="Ваша текущая аватарка")
        
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.text_input("Ваш системный Логин (Нельзя изменить):", value=st.session_state.username, disabled=True)
        new_nick = st.text_input("Ваш публичный Никнейм (Отображается в чатах):", value=current_nickname)
    with col_p2:
        uploaded_avatar = st.file_uploader("Загрузить новую картинку на аватарку:", type=["jpg", "png", "jpeg"])
    
    if st.button("Сохранить изменения в профиле", use_container_width=True):
        st.session_state.nickname = new_nick
        cursor.execute("UPDATE users SET nickname = %s WHERE uid = %s", (new_nick, st.session_state.user_uid))
        if uploaded_avatar:
            avatar_bytes = uploaded_avatar.read()
            cursor.execute("UPDATE users SET avatar = %s WHERE uid = %s", (avatar_bytes, st.session_state.user_uid))
        conn.commit()
        st.success("Профиль успешно обновлен!")
        st.rerun()
            
    if st.button("Выйти из аккаунта"):
        controller.remove("device_token")
        st.session_state.logged_in = False
        st.session_state.user_uid = None
        st.session_state.username = None
        st.session_state.nickname = None
        st.rerun()

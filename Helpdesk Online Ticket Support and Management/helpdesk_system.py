import streamlit as st
import sqlite3
import pandas as pd
import base64
from datetime import datetime

# Initialize database
conn = sqlite3.connect('helpdesk.db', check_same_thread=False)
cursor = conn.cursor()

# Create tables if not already created
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'user'
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT '',
    priority TEXT DEFAULT 'Low',
    created_date TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

# Add missing columns if they don't exist
try:
    cursor.execute("ALTER TABLE tickets ADD COLUMN priority TEXT DEFAULT 'Low'")
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE tickets ADD COLUMN created_date TEXT NOT NULL DEFAULT '1970-01-01 00:00:00'")
    conn.commit()
except sqlite3.OperationalError:
    pass

conn.commit()

# Helper functions
def register_user(username, password):
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    return cursor.fetchone()

def fetch_all_tickets():
    cursor.execute("SELECT id, title, description, status, priority, created_date FROM tickets")
    return cursor.fetchall()

def fetch_tickets(user_id):
    cursor.execute("SELECT id, title, description, status, priority, created_date FROM tickets WHERE user_id = ?", (user_id,))
    return cursor.fetchall()

def get_ticket_summary(user_id=None):
    if user_id:
        tickets = fetch_tickets(user_id)
    else:
        tickets = fetch_all_tickets()
    total_tickets = len(tickets)
    opened_tickets = len([t for t in tickets if t[3] == "Open"])
    in_progress_tickets = len([t for t in tickets if t[3] == "In Progress"])
    closed_tickets = len([t for t in tickets if t[3] == "Closed"])
    return total_tickets, opened_tickets, in_progress_tickets, closed_tickets

def submit_ticket(title, description, priority, user_id):
    created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO tickets (title, description, status, priority, created_date, user_id) VALUES (?, ?, '', ?, ?, ?)", (title, description, priority, created_date, user_id))
    conn.commit()

def update_status(ticket_id, new_status):
    cursor.execute("UPDATE tickets SET status = ? WHERE id = ?", (new_status, ticket_id))
    conn.commit()

def sort_df():
    st.session_state.df = st.session_state.df.sort_values(by="Status")

# Streamlit UI
st.set_page_config(page_title="Helpdesk Ticket System", layout="wide", initial_sidebar_state="expanded")

# Add custom styles for background and buttons
st.markdown(
    """
    <style>
    body {
        font-family: 'Roboto', sans-serif;
    }
    
    .homepage-background {
        background-image: url('./img1.png');
        background-size: cover;
        background-position: center;
        height: 100vh;
        color: white;
        display: flex;
        justify-content: center;
        align-items: center;
        text-align: center;
    }

    .stButton button {
        font-family: 'Roboto', sans-serif;
        background-color: #4c669f;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 8px 15px;
        font-weight: bold;
    }

    .stButton button:hover {
        background-color: #3b5998;
        cursor: pointer;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if 'user' in st.session_state:
    st.sidebar.markdown(f"**Logged in as:** {st.session_state['user'][1]}")
else:
    st.sidebar.markdown("**Not logged in**")

st.title("Helpdesk Ticket Management System")

menu = ["Home", "Login as User", "Register", "Login as Admin"]
if 'user' in st.session_state:
    menu.append("Dashboard")
choice = st.sidebar.selectbox("Menu", menu)

# Skip home and directly redirect to dashboard if user is logged in
if 'user' in st.session_state and choice == "Home":
    choice = "Dashboard"

if choice == "Home":
    st.markdown('<div class="home-background">', unsafe_allow_html=True)
    st.subheader("Welcome to the Helpdesk Ticket Management System")
    st.write("Use the menu to navigate through the application.")
    st.markdown('</div>', unsafe_allow_html=True)

elif choice == "Register":
    st.markdown('<div class="register-background">', unsafe_allow_html=True)
    st.subheader("Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if register_user(username, password):
            st.success("Registration successful! You can now log in.")
        else:
            st.error("Username already exists. Try a different one.")
    st.markdown('</div>', unsafe_allow_html=True)

elif choice == "Login as User":
    st.markdown('<div class="login-background">', unsafe_allow_html=True)
    st.subheader("User Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login as User"):
        user = login_user(username, password)
        if user:
            st.success(f"Welcome, {user[1]}!")
            st.session_state['user'] = user
            st.experimental_rerun()
        else:
            st.error("Invalid credentials. Please try again.")
    st.markdown('</div>', unsafe_allow_html=True)

elif choice == "Login as Admin":
    st.markdown('<div class="login-background">', unsafe_allow_html=True)
    st.subheader("Admin Login")
    username = st.text_input("Admin Username")
    password = st.text_input("Admin Password", type="password")
    if st.button("Login as Admin"):
        if username == "admin" and password == "admin@123":
            st.success("Welcome, Admin!")
            st.session_state['user'] = (0, "admin", "admin@123", "admin")
            st.experimental_rerun()
        else:
            st.error("Invalid admin credentials.")
    st.markdown('</div>', unsafe_allow_html=True)

elif choice == "Dashboard" and 'user' in st.session_state:
    user = st.session_state['user']
    if user[1] == "admin":
        st.subheader("Admin Dashboard - All Tickets")

        tickets = fetch_all_tickets()
        if tickets:
            df = pd.DataFrame(tickets, columns=["ID", "Title", "Description", "Status", "Priority", "Created Date"])
            st.session_state.df = df

            # Admin updates ticket status in real-time
            edited_df = st.data_editor(st.session_state.df, use_container_width=True, hide_index=True, height=212,
                column_config={'Status': st.column_config.SelectboxColumn(
                                            'Status',
                                            help='Ticket status',
                                            options=[ '', 'Open', 'In Progress', 'Closed' ],
                                            required=False,
                                            ),
                               'Priority': st.column_config.SelectboxColumn(
                                           'Priority',
                                            help='Priority',
                                            options=['High', 'Medium', 'Low'],
                                            required=True,
                                            ),
                             })

            total, opened, in_progress, closed = get_ticket_summary()

            st.markdown(f"### Ticket Summary")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total", total)
            col2.metric("Opened", opened)
            col3.metric("In Progress", in_progress)
            col4.metric("Closed", closed)

            # Show tickets that are closed
            closed_tickets = df[df['Status'] == "Closed"]
            st.write("### Closed Tickets")
            st.dataframe(closed_tickets)

            # Trigger page refresh to reflect status update
            if st.button("Save Changes"):
                for ticket in edited_df.itertuples():
                    update_status(ticket.ID, ticket.Status)
                st.experimental_rerun()

        else:
            st.info("No tickets to display.")

    else:
        st.subheader(f"Dashboard - Welcome {user[1]}")

        action = st.radio("Actions", ["Submit Ticket", "View Tickets"], horizontal=True)

        if action == "Submit Ticket":
            st.subheader("Submit a New Ticket")
            title = st.text_input("Title")
            description = st.text_area("Issue")
            priority = st.selectbox("Priority", ["Low", "Mid", "High"], index=0)
            if st.button("Submit"):
                submit_ticket(title, description, priority, user[0])
                st.success("Ticket submitted successfully!")

        elif action == "View Tickets":
            st.subheader("Your Tickets")
            tickets = fetch_tickets(user[0])
            if tickets:
                df = pd.DataFrame(tickets, columns=["ID", "Title", "Description", "Status", "Priority", "Created Date"])
                
                st.dataframe(df)
            else:
                st.info("No tickets to display.")





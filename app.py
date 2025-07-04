from flask import Flask, request, session, redirect, url_for, render_template_string
from markupsafe import escape
import json
import os
import threading
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'capiche_secret_2023'

# JSON File Paths
DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
ANNOUNCEMENTS_FILE = os.path.join(DATA_DIR, 'announcements.json')
POLLS_FILE = os.path.join(DATA_DIR, 'polls.json')
DICTIONARY_FILE = os.path.join(DATA_DIR, 'dictionary.json')

# Initialize data directories and files if not exist
os.makedirs(DATA_DIR, exist_ok=True)

# File lock for thread safety
file_lock = threading.Lock()

def init_file(file_path, default_data):
    with file_lock:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default_data, f, indent=2)

# Initialize with plaintext passwords
init_file(USERS_FILE, [
    {'username': 'adrian', 'password': 'adrian123', 'role': 'Leader', 'votePower': 6, 'muted': False},
    {'username': 'ish', 'password': 'ishpass', 'role': 'Mod', 'votePower': 4, 'muted': False},
    {'username': 'member1', 'password': 'temp1', 'role': 'Member', 'votePower': 1, 'muted': False}
])
init_file(ANNOUNCEMENTS_FILE, [])
init_file(POLLS_FILE, [])
init_file(DICTIONARY_FILE, [])

# Helper Functions
def load_json(file_path):
    with file_lock:
        with open(file_path, 'r') as f:
            return json.load(f)

def save_json(file_path, data):
    with file_lock:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

def get_user(username):
    users = load_json(USERS_FILE)
    return next((u for u in users if u['username'] == username), None)

# Sanitize output for HTML
def safe_display(text):
    return escape(str(text))

# Role-based access decorators
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

def require_mod(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = session.get('user', {})
        if user.get('role') not in ['Leader', 'Mod']:
            return 'Forbidden', 403
        return f(*args, **kwargs)
    return decorated

def require_leader(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('user', {}).get('role') != 'Leader':
            return 'Forbidden', 403
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = session.get('user', {})
        if user.get('username') not in ['adrian', 'ish']:
            return 'Forbidden', 403
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>GabeeshSocial</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root { --color-green: #22c55e; }
        body { font-family: 'Montserrat', 'Inter', sans-serif; }
        .btn-green { background-color: var(--color-green); }
        .glass {
            background: rgba(31, 41, 55, 0.92);
            box-shadow: 0 8px 32px 0 rgba(31, 41, 55, 0.37);
            backdrop-filter: blur(6px);
            border-radius: 1.5rem;
            border: 1px solid rgba(34,197,94,0.2);
        }
        .gradient-bg {
            background: linear-gradient(135deg, #22c55e 0%, #2563eb 100%);
        }
        .text-contrast { color: #f3f4f6; }
        .text-contrast-secondary { color: #d1d5db; }
        .input-dark {
            background-color: #1f2937;
            color: #f3f4f6;
            border: 1px solid #374151;
        }
        .input-dark::placeholder { color: #9ca3af; }
    </style>
</head>
<body class="gradient-bg min-h-screen flex items-center justify-center">
    <div class="container mx-auto px-4 py-12">
        <div class="max-w-md mx-auto glass p-10">
            <h1 class="text-4xl font-extrabold text-center mb-6 text-contrast drop-shadow-lg">GabeeshSocial</h1>
            <p class="text-center mb-8 text-contrast-secondary">Private community for Gabeesh members only</p>
            <div class="space-y-4">
                <a href="/login" class="block w-full btn-green text-white text-center py-3 rounded-lg font-semibold shadow-lg hover:scale-105 transition transform duration-150">Login</a>
            </div>
        </div>
    </div>
</body>
</html>
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_json(USERS_FILE)
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        if user:
            session['authenticated'] = True
            session['user'] = {
                'username': user['username'],
                'role': user['role'],
                'votePower': user['votePower'],
                'muted': user['muted']
            }
            return redirect('/dashboard')
        error = 'Invalid credentials'
    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Login - CapicheSocial</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --color-green: #22c55e; }}
        body {{ font-family: 'Montserrat', 'Inter', sans-serif; }}
        .btn-green {{ background-color: var(--color-green); }}
        .glass {{
            background: rgba(31, 41, 55, 0.92);
            box-shadow: 0 8px 32px 0 rgba(31, 41, 55, 0.37);
            backdrop-filter: blur(6px);
            border-radius: 1.5rem;
            border: 1px solid rgba(34,197,94,0.2);
        }}
        .gradient-bg {{
            background: linear-gradient(135deg, #22c55e 0%, #2563eb 100%);
        }}
        .text-contrast {{ color: #f3f4f6; }}
        .text-contrast-secondary {{ color: #d1d5db; }}
        .input-dark {{
            background-color: #1f2937;
            color: #f3f4f6;
            border: 1px solid #374151;
        }}
        .input-dark::placeholder {{ color: #9ca3af; }}
    </style>
</head>
<body class="gradient-bg min-h-screen flex items-center justify-center">
    <div class="container mx-auto px-4 py-12">
        <div class="max-w-md mx-auto glass p-10">
            <h2 class="text-3xl font-bold mb-6 text-contrast text-center">Login to CapicheSocial</h2>
            {f'<p class="text-red-400 mb-4 text-center">{error}</p>' if error else ''}
            <form method="POST" class="space-y-6">
                <div>
                    <label class="block text-sm font-medium mb-1 text-contrast-secondary">Username</label>
                    <input type="text" name="username" required class="w-full px-3 py-2 input-dark rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1 text-contrast-secondary">Password</label>
                    <input type="password" name="password" required class="w-full px-3 py-2 input-dark rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500">
                </div>
                <button type="submit" class="w-full btn-green text-white py-2 rounded-lg font-semibold shadow-lg hover:scale-105 transition transform duration-150">Login</button>
            </form>
        </div>
    </div>
</body>
</html>
'''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
@require_mod
def register():
    success = ''
    error = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'Member')
        users = load_json(USERS_FILE)
        if any(u['username'] == username for u in users):
            error = 'Username already exists'
        else:
            users.append({
                'username': username,
                'password': password,
                'role': role,
                'votePower': 1,
                'muted': False
            })
            save_json(USERS_FILE, users)
            success = 'User registered successfully'
    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Register - CapicheSocial</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --color-green: #22c55e; }}
        body {{ font-family: 'Montserrat', 'Inter', sans-serif; }}
        .btn-green {{ background-color: var(--color-green); }}
        .glass {{
            background: rgba(31, 41, 55, 0.92);
            box-shadow: 0 8px 32px 0 rgba(31, 41, 55, 0.37);
            backdrop-filter: blur(6px);
            border-radius: 1.5rem;
            border: 1px solid rgba(34,197,94,0.2);
        }}
        .gradient-bg {{
            background: linear-gradient(135deg, #22c55e 0%, #2563eb 100%);
        }}
        .text-contrast {{ color: #f3f4f6; }}
        .text-contrast-secondary {{ color: #d1d5db; }}
        .input-dark {{
            background-color: #1f2937;
            color: #f3f4f6;
            border: 1px solid #374151;
        }}
        .input-dark::placeholder {{ color: #9ca3af; }}
    </style>
</head>
<body class="gradient-bg min-h-screen flex items-center justify-center">
    <div class="container mx-auto px-4 py-12">
        <div class="max-w-md mx-auto glass p-10">
            <h2 class="text-3xl font-bold mb-6 text-contrast text-center">Register New User</h2>
            {f'<p class="text-green-500 mb-4">{success}</p>' if success else ''}
            {f'<p class="text-red-500 mb-4">{error}</p>' if error else ''}
            <form method="POST" class="space-y-4">
                <div><label class="block text-sm font-medium mb-1">Username</label>
                    <input type="text" name="username" required class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md">
                </div>
                <div><label class="block text-sm font-medium mb-1">Password</label>
                    <input type="password" name="password" required class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md">
                </div>
                <div><label class="block text-sm font-medium mb-1">Role</label>
                    <select name="role" class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md">
                        <option value="Member">Member</option>
                        <option value="Mod">Moderator</option>
                        <option value="Leader">Leader</option>
                    </select>
                </div>
                <button type="submit" class="w-full btn-green text-white py-2 rounded-md transition">Register</button>
            </form>
        </div>
    </div>
</body>
</html>
'''

@app.route('/dashboard', methods=['GET', 'POST'])
@require_auth
def dashboard():
    user = session['user']
    message = ''
    error = ''
    # Only adrian and ish can add new members from dashboard
    if user['username'] in ['adrian', 'ish'] and request.method == 'POST':
        new_username = request.form.get('new_username', '').strip()
        new_password = request.form.get('new_password', '').strip()
        new_vote_power = request.form.get('new_vote_power', '').strip()
        try:
            vote_power = int(new_vote_power)
            if vote_power < 1 or vote_power > 6:
                raise ValueError()
        except Exception:
            vote_power = 1
        if not new_username or not new_password:
            error = 'Username and password are required.'
        else:
            users = load_json(USERS_FILE)
            if any(u['username'] == new_username for u in users):
                error = 'Username already exists.'
            else:
                users.append({
                    'username': new_username,
                    'password': new_password,
                    'role': 'Member',
                    'votePower': vote_power,
                    'muted': False
                })
                save_json(USERS_FILE, users)
                message = f'User {new_username} created successfully with vote weight {vote_power}.'

    create_member_form = ''
    if user['username'] in ['adrian', 'ish']:
        create_member_form = f'''
        <div class="glass p-8 mt-8">
            <h2 class="text-2xl font-bold mb-4 text-contrast">Create New Member</h2>
            {f'<p class="text-green-400 mb-2">{message}</p>' if message else ''}
            {f'<p class="text-red-400 mb-2">{error}</p>' if error else ''}
            <form method="POST" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium mb-1 text-contrast-secondary">Username</label>
                    <input type="text" name="new_username" required class="w-full px-3 py-2 input-dark rounded-md">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1 text-contrast-secondary">Password</label>
                    <input type="password" name="new_password" required class="w-full px-3 py-2 input-dark rounded-md">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1 text-contrast-secondary">Vote Weight</label>
                    <input type="number" name="new_vote_power" min="1" max="6" value="1" required class="w-full px-3 py-2 input-dark rounded-md">
                </div>
                <button type="submit" class="btn-green text-white px-4 py-2 rounded-md font-semibold shadow-lg hover:scale-105 transition">Create Member</button>
            </form>
        </div>
        '''

    nav_tabs = f'''
        <div class="flex space-x-4 mb-8">
            <a href="/announcements" class="btn-green text-white px-4 py-2 rounded-lg font-semibold shadow hover:scale-105 transition">Announcements</a>
            <a href="/polls" class="btn-green text-white px-4 py-2 rounded-lg font-semibold shadow hover:scale-105 transition">Polls</a>
            <a href="/dictionary" class="btn-green text-white px-4 py-2 rounded-lg font-semibold shadow hover:scale-105 transition">Dictionary</a>
        </div>
    '''

    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - GabeeshSocial</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --color-green: #22c55e; }}
        body {{ font-family: 'Montserrat', 'Inter', sans-serif; }}
        .btn-green {{ background-color: var(--color-green); }}
        .glass {{
            background: rgba(31, 41, 55, 0.92);
            box-shadow: 0 8px 32px 0 rgba(31, 41, 55, 0.37);
            backdrop-filter: blur(6px);
            border-radius: 1.5rem;
            border: 1px solid rgba(34,197,94,0.2);
        }}
        .gradient-bg {{
            background: linear-gradient(135deg, #22c55e 0%, #2563eb 100%);
        }}
        .text-contrast {{ color: #f3f4f6; }}
        .text-contrast-secondary {{ color: #d1d5db; }}
        .input-dark {{
            background-color: #1f2937;
            color: #f3f4f6;
            border: 1px solid #374151;
        }}
        .input-dark::placeholder {{ color: #9ca3af; }}
    </style>
</head>
<body class="gradient-bg min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-4xl font-extrabold text-contrast drop-shadow-lg">Welcome, {safe_display(user['username'])}</h1>
            <a href="/logout" class="text-red-400 hover:underline font-semibold">Logout</a>
        </div>
        {nav_tabs}
        <div class="grid md:grid-cols-2 gap-8">
            <div class="glass p-8">
                <h2 class="text-2xl font-semibold mb-4 text-contrast">Announcements</h2>
                <a href="/announcements" class="btn-green text-white px-4 py-2 rounded-lg inline-block mb-4 font-semibold shadow-lg hover:scale-105 transition">View Announcements</a>
                <p class="text-sm text-contrast-secondary">Check for updates from Adrian</p>
            </div>
            <div class="glass p-8">
                <h2 class="text-2xl font-semibold mb-4 text-contrast">Polls</h2>
                <a href="/polls" class="btn-green text-white px-4 py-2 rounded-lg inline-block mb-4 font-semibold shadow-lg hover:scale-105 transition">Vote Now</a>
                <p class="text-sm text-contrast-secondary">Your vote carries weight: {user['votePower']}</p>
            </div>
        </div>
        {create_member_form}
    </div>
</body>
</html>
'''

@app.route('/admin')
@require_admin
def admin():
    users = load_json(USERS_FILE)
    rows_html = ''
    for u in users:
        mute_action = "unmute" if u["muted"] else "mute"
        mute_text = "Unmute" if u["muted"] else "Mute"
        status_text = "Muted" if u["muted"] else "Active"
        options_html = ''.join(f'<option value="{i}" {"selected" if i == u["votePower"] else ""}>{i}</option>' for i in range(1, 6))
        role_options = ''.join(f'<option value="{r}" {"selected" if r == u["role"] else ""}>{r}</option>' for r in ['Member', 'Mod', 'Leader'])

        rows_html += f'''
        <tr class="hover:bg-gray-700">
            <td class="px-6 py-4 whitespace-nowrap">{safe_display(u["username"])}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <form action="/assign-role" method="POST" class="inline">
                    <input type="hidden" name="username" value="{safe_display(u["username"])}">
                    <select name="role" onchange="this.form.submit()" class="bg-gray-700 border border-gray-600 text-white rounded px-2 py-1">
                        {role_options}
                    </select>
                </form>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <form action="/assign-vote" method="POST" class="inline">
                    <input type="hidden" name="username" value="{safe_display(u["username"])}">
                    <select name="power" onchange="this.form.submit()" class="bg-gray-700 border border-gray-600 text-white rounded px-2 py-1">
                        <option value="">Vote Power</option>
                        {options_html}
                    </select>
                </form>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">{status_text}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <form action="/{mute_action}-user" method="POST" class="inline">
                    <input type="hidden" name="username" value="{safe_display(u["username"])}">
                    <button type="submit" class="bg-yellow-600 hover:bg-yellow-700 text-white px-2 py-1 rounded">
                        {mute_text}
                    </button>
                </form>
                <form action="/delete-user" method="POST" class="inline" onsubmit="return confirm('Delete {safe_display(u['username'])}?')">
                    <input type="hidden" name="username" value="{safe_display(u["username"])}">
                    <button type="submit" class="bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded ml-2">
                        Delete
                    </button>
                </form>
                <form action="/reset-password" method="POST" class="inline">
                    <input type="hidden" name="username" value="{safe_display(u["username"])}">
                    <input type="text" name="new_password" placeholder="New Password" class="bg-gray-700 border border-gray-600 text-white rounded px-2 py-1">
                    <button type="submit" class="bg-purple-600 hover:bg-purple-700 text-white px-2 py-1 rounded ml-2">
                        Reset
                    </button>
                </form>
            </td>
        </tr>
        '''

    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel - CapicheSocial</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --color-green: #22c55e; }}
        body {{ font-family: 'Montserrat', 'Inter', sans-serif; }}
        .btn-green {{ background-color: var(--color-green); }}
        .glass {{
            background: rgba(31, 41, 55, 0.92);
            box-shadow: 0 8px 32px 0 rgba(31, 41, 55, 0.37);
            backdrop-filter: blur(6px);
            border-radius: 1.5rem;
            border: 1px solid rgba(34,197,94,0.2);
        }}
        .gradient-bg {{
            background: linear-gradient(135deg, #22c55e 0%, #2563eb 100%);
        }}
        .text-contrast {{ color: #f3f4f6; }}
        .text-contrast-secondary {{ color: #d1d5db; }}
        .input-dark {{
            background-color: #1f2937;
            color: #f3f4f6;
            border: 1px solid #374151;
        }}
        .input-dark::placeholder {{ color: #9ca3af; }}
    </style>
</head>
<body class="gradient-bg min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-3xl font-bold">Admin Panel</h1>
            <a href="/logout" class="text-red-500 hover:underline">Logout</a>
        </div>

        <div class="mb-6 bg-gray-800 p-6 rounded-lg shadow-lg">
            <h2 class="text-xl font-semibold mb-4">Create New User</h2>
            <a href="/register" class="btn-green text-white px-4 py-2 rounded-md inline-block mb-4">Register New User</a>
        </div>

        <div class="bg-gray-800 rounded-lg shadow-lg overflow-hidden">
            <table class="min-w-full divide-y divide-gray-700">
                <thead class="bg-gray-700">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Username</th>
                        <th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Role</th>
                        <th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Vote Power</th>
                        <th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Status</th>
                        <th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Actions</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-700">
                    {rows_html}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
'''

@app.route('/assign-role', methods=['POST'])
@require_admin
def assign_role():
    username = request.form.get('username')
    new_role = request.form.get('role')
    users = load_json(USERS_FILE)
    for u in users:
        if u['username'] == username:
            if u['username'] in ['adrian', 'ish']: continue
            u['role'] = new_role
            break
    save_json(USERS_FILE, users)
    return redirect('/admin')

@app.route('/assign-vote', methods=['POST'])
@require_admin
def assign_vote():
    username = request.form.get('username')
    power = int(request.form.get('power'))
    users = load_json(USERS_FILE)
    for u in users:
        if u['username'] == username:
            u['votePower'] = power
            break
    save_json(USERS_FILE, users)
    return redirect('/admin')

@app.route('/mute-user', methods=['POST'])
@require_admin
def mute_user():
    username = request.form.get('username')
    users = load_json(USERS_FILE)
    for u in users:
        if u['username'] == username:
            u['muted'] = True
            break
    save_json(USERS_FILE, users)
    return redirect('/admin')

@app.route('/unmute-user', methods=['POST'])
@require_admin
def unmute_user():
    username = request.form.get('username')
    users = load_json(USERS_FILE)
    for u in users:
        if u['username'] == username:
            u['muted'] = False
            break
    save_json(USERS_FILE, users)
    return redirect('/admin')

@app.route('/delete-user', methods=['POST'])
@require_admin
def delete_user():
    username = request.form.get('username')
    users = load_json(USERS_FILE)
    users = [u for u in users if u['username'] != username]
    save_json(USERS_FILE, users)
    return redirect('/admin')

@app.route('/reset-password', methods=['POST'])
@require_admin
def reset_password():
    username = request.form.get('username')
    new_password = request.form.get('new_password')
    users = load_json(USERS_FILE)
    for u in users:
        if u['username'] == username:
            u['password'] = new_password
            break
    save_json(USERS_FILE, users)
    return redirect('/admin')

@app.route('/admin/content')
@require_admin
def admin_content():
    announcements = load_json(ANNOUNCEMENTS_FILE)
    polls = load_json(POLLS_FILE)
    announcements.sort(key=lambda x: x['timestamp'], reverse=True)
    polls.sort(key=lambda x: x['expires_at'], reverse=True)

    # Build announcements rows
    announcements_rows = ''.join(
        f'''
        <tr class="hover:bg-gray-700">
            <td class="px-6 py-4">{a["title"]}</td>
            <td class="px-6 py-4">{a["author"]}</td>
            <td class="px-6 py-4">{a["timestamp"]}</td>
            <td class="px-6 py-4">
                <form action="/delete-announcement" method="POST" class="inline">
                    <input type="hidden" name="id" value="{a["title"]}">
                    <button type="submit" class="bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded">
                        Delete
                    </button>
                </form>
            </td>
        </tr>
        ''' for a in announcements
    )

    # Build polls rows
    polls_rows = ''.join(
        f'''
        <tr class="hover:bg-gray-700">
            <td class="px-6 py-4">{p["question"]}</td>
            <td class="px-6 py-4">{p["expires_at"]}</td>
            <td class="px-6 py-4">
                <form action="/delete-poll" method="POST" class="inline">
                    <input type="hidden" name="id" value="{p["id"]}">
                    <button type="submit" class="bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded">
                        Delete
                    </button>
                </form>
                <a href="/edit-poll/{p["id"]}" class="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded ml-2">
                    Edit
                </a>
            </td>
            <td class="px-6 py-4">
                <details>
                    <summary class="cursor-pointer text-green-500">View Votes</summary>
                    <ul class="mt-2">
                        {''.join(f'<li>{voter} ➔ {p["options"][vote_idx]}</li>' for voter, vote_idx in p.get("votes", {}).items())}
                    </ul>
                </details>
            </td>
        </tr>
        ''' for p in polls
    )

    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Content Admin - CapicheSocial</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --color-green: #22c55e; }}
        body {{ font-family: 'Montserrat', 'Inter', sans-serif; }}
        .btn-green {{ background-color: var(--color-green); }}
        .glass {{
            background: rgba(31, 41, 55, 0.92);
            box-shadow: 0 8px 32px 0 rgba(31, 41, 55, 0.37);
            backdrop-filter: blur(6px);
            border-radius: 1.5rem;
            border: 1px solid rgba(34,197,94,0.2);
        }}
        .gradient-bg {{
            background: linear-gradient(135deg, #22c55e 0%, #2563eb 100%);
        }}
        .text-contrast {{ color: #f3f4f6; }}
        .text-contrast-secondary {{ color: #d1d5db; }}
        .input-dark {{
            background-color: #1f2937;
            color: #f3f4f6;
            border: 1px solid #374151;
        }}
        .input-dark::placeholder {{ color: #9ca3af; }}
    </style>
</head>
<body class="gradient-bg min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-3xl font-bold">Content Management</h1>
            <a href="/admin" class="text-blue-500 hover:underline">Back to User Admin</a>
        </div>

        <!-- Announcements -->
        <div class="mb-12">
            <h2 class="text-2xl font-semibold mb-4">Announcements</h2>
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-700">
                    <thead class="bg-gray-700">
                        <tr>
                            <th>Title</th>
                            <th>Author</th>
                            <th>Date</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-700">
                        {announcements_rows}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Polls -->
        <div>
            <h2 class="text-2xl font-semibold mb-4">Polls</h2>
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-700">
                    <thead class="bg-gray-700">
                        <tr>
                            <th>Question</th>
                            <th>Expires</th>
                            <th>Actions</th>
                            <th>Votes Detail</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-700">
                        {polls_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
'''

@app.route('/edit-poll/<int:poll_id>', methods=['GET', 'POST'])
@require_admin
def edit_poll(poll_id):
    polls = load_json(POLLS_FILE)
    poll = next((p for p in polls if p['id'] == poll_id), None)
    if not poll:
        return 'Poll Not Found', 404

    if request.method == 'POST':
        new_expires = request.form.get('expires_at')
        if new_expires:
            poll['expires_at'] = new_expires
            save_json(POLLS_FILE, polls)
            return redirect('/admin/content')

    default_expires = poll['expires_at'].replace('T', ' ')[:16]

    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Edit Poll - CapicheSocial</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --color-green: #22c55e; }}
        body {{ font-family: 'Montserrat', 'Inter', sans-serif; }}
        .btn-green {{ background-color: var(--color-green); }}
        .glass {{
            background: rgba(31, 41, 55, 0.92);
            box-shadow: 0 8px 32px 0 rgba(31, 41, 55, 0.37);
            backdrop-filter: blur(6px);
            border-radius: 1.5rem;
            border: 1px solid rgba(34,197,94,0.2);
        }}
        .gradient-bg {{
            background: linear-gradient(135deg, #22c55e 0%, #2563eb 100%);
        }}
        .text-contrast {{ color: #f3f4f6; }}
        .text-contrast-secondary {{ color: #d1d5db; }}
        .input-dark {{
            background-color: #1f2937;
            color: #f3f4f6;
            border: 1px solid #374151;
        }}
        .input-dark::placeholder {{ color: #9ca3af; }}
    </style>
</head>
<body class="gradient-bg min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold mb-6">Edit Poll: {poll["question"]}</h1>
        <form method="POST" class="max-w-md">
            <div class="mb-4">
                <label class="block text-sm font-medium mb-2">New Expiration Date</label>
                <input type="datetime-local" name="expires_at" value="{default_expires}"
                       class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md">
            </div>
            <button type="submit" class="btn-green text-white px-4 py-2 rounded-md">Update Expiration</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/delete-announcement', methods=['POST'])
@require_admin
def delete_announcement():
    title = request.form.get('id')
    announcements = load_json(ANNOUNCEMENTS_FILE)
    announcements = [a for a in announcements if a['title'] != title]
    save_json(ANNOUNCEMENTS_FILE, announcements)
    return redirect('/admin/content')

@app.route('/delete-poll', methods=['POST'])
@require_admin
def delete_poll():
    poll_id = int(request.form.get('id'))
    polls = load_json(POLLS_FILE)
    polls = [p for p in polls if p['id'] != poll_id]
    save_json(POLLS_FILE, polls)
    return redirect('/admin/content')

@app.route('/create-announcement', methods=['GET', 'POST'])
@require_mod
def create_announcement():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        author = session['user']['username']
        timestamp = datetime.now().isoformat()
        announcements = load_json(ANNOUNCEMENTS_FILE)
        announcements.append({'title': title, 'content': content, 'author': author, 'timestamp': timestamp})
        save_json(ANNOUNCEMENTS_FILE, announcements)
        return redirect('/announcements')
    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Create Announcement - CapicheSocial</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --color-green: #22c55e; }}
        body {{ font-family: 'Montserrat', 'Inter', sans-serif; }}
        .btn-green {{ background-color: var(--color-green); }}
        .glass {{
            background: rgba(31, 41, 55, 0.92);
            box-shadow: 0 8px 32px 0 rgba(31, 41, 55, 0.37);
            backdrop-filter: blur(6px);
            border-radius: 1.5rem;
            border: 1px solid rgba(34,197,94,0.2);
        }}
        .gradient-bg {{
            background: linear-gradient(135deg, #22c55e 0%, #2563eb 100%);
        }}
        .text-contrast {{ color: #f3f4f6; }}
        .text-contrast-secondary {{ color: #d1d5db; }}
        .input-dark {{
            background-color: #1f2937;
            color: #f3f4f6;
            border: 1px solid #374151;
        }}
        .input-dark::placeholder {{ color: #9ca3af; }}
    </style>
</head>
<body class="gradient-bg min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-3xl font-bold">Create New Announcement</h1>
            <a href="/logout" class="text-red-500 hover:underline">Logout</a>
        </div>
        <div class="bg-gray-800 rounded-lg shadow-lg p-6 max-w-2xl mx-auto">
            <form method="POST" class="space-y-4">
                <div><label class="block text-sm font-medium mb-1">Title</label>
                    <input type="text" name="title" required class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md">
                </div>
                <div><label class="block text-sm font-medium mb-1">Content</label>
                    <textarea name="content" rows="6" required class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md"></textarea>
                </div>
                <button type="submit" class="w-full btn-green text-white py-2 rounded-md transition">Post Announcement</button>
            </form>
        </div>
    </div>
</body>
</html>
'''

@app.route('/create-poll', methods=['GET', 'POST'])
@require_mod
def create_poll():
    if request.method == 'POST':
        question = request.form.get('question')
        options = [request.form.get(f'option{i}') for i in range(5)]
        options = [opt for opt in options if opt]
        expires_at = request.form.get('expires_at')
        if not question or len(options) < 2 or not expires_at:
            return 'Missing required fields', 400
        polls = load_json(POLLS_FILE)
        poll_id = max([p['id'] for p in polls], default=0) + 1
        polls.append({
            'id': poll_id,
            'question': question,
            'options': options,
            'results': [0]*len(options),
            'expires_at': expires_at,
            'votes': {}
        })
        save_json(POLLS_FILE, polls)
        return redirect('/polls')

    default_expires = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M")

    # Build options HTML separately to avoid nested f-string issues
    options_html = ''.join(
        f'<input type="text" name="option{i}" placeholder="Option {i+1}" required class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md mb-1">\n'
        for i in range(5)
    )

    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Create Poll - CapicheSocial</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --color-green: #22c55e; }}
        body {{ font-family: 'Montserrat', 'Inter', sans-serif; }}
        .btn-green {{ background-color: var(--color-green); }}
        .glass {{
            background: rgba(31, 41, 55, 0.92);
            box-shadow: 0 8px 32px 0 rgba(31, 41, 55, 0.37);
            backdrop-filter: blur(6px);
            border-radius: 1.5rem;
            border: 1px solid rgba(34,197,94,0.2);
        }}
        .gradient-bg {{
            background: linear-gradient(135deg, #22c55e 0%, #2563eb 100%);
        }}
        .text-contrast {{ color: #f3f4f6; }}
        .text-contrast-secondary {{ color: #d1d5db; }}
        .input-dark {{
            background-color: #1f2937;
            color: #f3f4f6;
            border: 1px solid #374151;
        }}
        .input-dark::placeholder {{ color: #9ca3af; }}
    </style>
</head>
<body class="gradient-bg min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold mb-6">Create New Poll</h1>
        <form method="POST" class="max-w-2xl mx-auto space-y-6">
            <div><label class="block text-sm font-medium mb-1">Poll Question</label>
                <input type="text" name="question" required class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md">
            </div>
            <div class="space-y-2">
                <label class="block text-sm font-medium mb-1">Options</label>
                {options_html}
            </div>
            <div><label class="block text-sm font-medium mb-1">Expiration Date</label>
                <input type="datetime-local" name="expires_at" value="{default_expires}" class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md">
            </div>
            <button type="submit" class="btn-green text-white px-6 py-3 rounded-md">Create Poll</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/dictionary', methods=['GET', 'POST'])
@require_auth
def dictionary():
    user = session['user']
    can_add = user['username'] in ['adrian', 'ish']
    message = ''
    error = ''
    if can_add and request.method == 'POST':
        word = request.form.get('word', '').strip()
        definition = request.form.get('definition', '').strip()
        if not word or not definition:
            error = "Both word and definition are required."
        else:
            dictionary = load_json(DICTIONARY_FILE)
            if any(entry['word'].lower() == word.lower() for entry in dictionary):
                error = "That word already exists in the dictionary."
            else:
                dictionary.append({'word': word, 'definition': definition, 'author': user['username'], 'timestamp': datetime.now().isoformat()})
                save_json(DICTIONARY_FILE, dictionary)
                message = f'Word "{word}" added successfully.'

    dictionary = load_json(DICTIONARY_FILE)
    dictionary.sort(key=lambda x: x['word'].lower())
    entries_html = ''.join(
        f'''
        <div class="glass p-4 mb-4">
            <div class="flex justify-between items-center">
                <span class="font-bold text-contrast text-lg">{safe_display(entry["word"])}</span>
                <span class="text-xs text-gray-400">by {safe_display(entry["author"])} on {safe_display(entry["timestamp"]).split("T")[0]}</span>
            </div>
            <div class="text-contrast-secondary mt-2">{safe_display(entry["definition"])}</div>
        </div>
        ''' for entry in dictionary
    )
    add_form = ''
    if can_add:
        add_form = f'''
        <div class="glass p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4 text-contrast">Add to Dictionary</h2>
            {f'<p class="text-green-400 mb-2">{message}</p>' if message else ''}
            {f'<p class="text-red-400 mb-2">{error}</p>' if error else ''}
            <form method="POST" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium mb-1 text-contrast-secondary">Word</label>
                    <input type="text" name="word" required class="w-full px-3 py-2 input-dark rounded-md">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1 text-contrast-secondary">Definition</label>
                    <textarea name="definition" required class="w-full px-3 py-2 input-dark rounded-md"></textarea>
                </div>
                <button type="submit" class="btn-green text-white px-4 py-2 rounded-md font-semibold shadow-lg hover:scale-105 transition">Add Word</button>
            </form>
        </div>
        '''
    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Dictionary - GabeeshSocial</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --color-green: #22c55e; }}
        body {{ font-family: 'Montserrat', 'Inter', sans-serif; }}
        .btn-green {{ background-color: var(--color-green); }}
        .glass {{
            background: rgba(31, 41, 55, 0.92);
            box-shadow: 0 8px 32px 0 rgba(31, 41, 55, 0.37);
            backdrop-filter: blur(6px);
            border-radius: 1.5rem;
            border: 1px solid rgba(34,197,94,0.2);
        }}
        .gradient-bg {{
            background: linear-gradient(135deg, #22c55e 0%, #2563eb 100%);
        }}
        .text-contrast {{ color: #f3f4f6; }}
        .text-contrast-secondary {{ color: #d1d5db; }}
        .input-dark {{
            background-color: #1f2937;
            color: #f3f4f6;
            border: 1px solid #374151;
        }}
        .input-dark::placeholder {{ color: #9ca3af; }}
    </style>
</head>
<body class="gradient-bg min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-3xl font-bold text-contrast">Gabeesh Dictionary</h1>
            <a href="/dashboard" class="text-blue-400 hover:underline">Back to Dashboard</a>
        </div>
        {add_form}
        <div>
            <h2 class="text-xl font-semibold mb-4 text-contrast">All Words</h2>
            {entries_html if entries_html else '<p class="text-contrast-secondary">No words in the dictionary yet.</p>'}
        </div>
    </div>
</body>
</html>
'''

@app.route('/announcements')
@require_auth
def announcements_page():
    announcements = load_json(ANNOUNCEMENTS_FILE)
    user = session['user']
    announcements_html = ''.join(f'''
        <div class="glass p-6 mb-6">
            <h3 class="text-lg font-bold mb-1 text-contrast">{safe_display(a["title"])}</h3>
            <p class="text-contrast-secondary mb-2">{safe_display(a["content"])}</p>
            <p class="text-xs text-gray-400">Posted by {safe_display(a["author"])} on {a["timestamp"]}</p>
        </div>
    ''' for a in announcements)
    no_announcements = '<p class="text-contrast-secondary">No announcements yet</p>' if not announcements else ''
    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Announcements - GabeeshSocial</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --color-green: #22c55e; }}
        body {{ font-family: 'Montserrat', 'Inter', sans-serif; }}
        .btn-green {{ background-color: var(--color-green); }}
        .glass {{
            background: rgba(31, 41, 55, 0.92);
            box-shadow: 0 8px 32px 0 rgba(31, 41, 55, 0.37);
            backdrop-filter: blur(6px);
            border-radius: 1.5rem;
            border: 1px solid rgba(34,197,94,0.2);
        }}
        .gradient-bg {{
            background: linear-gradient(135deg, #22c55e 0%, #2563eb 100%);
        }}
        .text-contrast {{ color: #f3f4f6; }}
        .text-contrast-secondary {{ color: #d1d5db; }}
    </style>
</head>
<body class="gradient-bg min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-3xl font-bold text-contrast">Announcements</h1>
            <a href="/logout" class="text-red-400 hover:underline">Logout</a>
        </div>
        <div class="mb-8">
            <h2 class="text-xl font-semibold mb-4 text-contrast">Recent Updates</h2>
            {f'<a href="/create-announcement" class="btn-green text-white px-4 py-2 rounded-md inline-block mb-4">Create Announcement</a>' if user['role'] in ["Leader", "Mod"] else ''}
            <div class="space-y-6">
                {announcements_html}
                {no_announcements}
            </div>
        </div>
    </div>
</body>
</html>
'''

@app.route('/polls', methods=['GET', 'POST'])
@require_auth
def polls_page():
    user = session['user']
    username = user['username']
    vote_power = user['votePower']
    polls = load_json(POLLS_FILE)
    now = datetime.now()

    if request.method == 'POST':
        poll_id = int(request.form.get('poll_id'))
        choice = int(request.form.get('choice'))
        for poll in polls:
            if poll['id'] == poll_id:
                expires_at = datetime.fromisoformat(poll['expires_at'])
                if expires_at > now and username not in poll.get('votes', {}):
                    poll.setdefault('votes', {})[username] = choice
                    poll['results'][choice] += vote_power
                    break
        save_json(POLLS_FILE, polls)
        return redirect('/polls')

    polls_html = ''
    for p in polls:
        options_html = ''
        for i, opt in enumerate(p["options"]):
            is_disabled = username in p.get("votes", {}) or datetime.fromisoformat(p["expires_at"]) <= now
            options_html += f'''
            <div class="flex items-center mb-1">
                <input type="radio" name="choice" value="{i}" id="choice-{p["id"]}-{i}" {"disabled" if is_disabled else ""} class="mr-2 accent-green-500">
                <label for="choice-{p["id"]}-{i}" class="text-contrast-secondary">
                    {safe_display(opt)} <span class="text-xs text-gray-400">({p["results"][i]} votes)</span>
                </label>
            </div>
            '''
        is_button_disabled = username in p.get("votes", {}) or datetime.fromisoformat(p["expires_at"]) <= now
        polls_html += f'''
        <div class="glass p-6 mb-8">
            <h2 class="text-xl font-semibold mb-2 text-contrast">{safe_display(p["question"])}</h2>
            <p class="text-sm text-gray-400 mb-4">Expires: {p["expires_at"]}</p>
            <form method="POST" class="space-y-3">
                <input type="hidden" name="poll_id" value="{p["id"]}">
                {options_html}
                <button type="submit" class="mt-4 btn-green text-white px-4 py-1 rounded-md inline-block font-semibold shadow-lg hover:scale-105 transition" {"disabled" if is_button_disabled else ""}>
                    Vote
                </button>
            </form>
        </div>
        '''
    no_polls = '<p class="text-contrast-secondary">No active polls</p>' if not polls else ''

    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Polls - CapicheSocial</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --color-green: #22c55e; }}
        body {{ font-family: 'Montserrat', 'Inter', sans-serif; }}
        .btn-green {{ background-color: var(--color-green); }}
        .glass {{
            background: rgba(31, 41, 55, 0.92);
            box-shadow: 0 8px 32px 0 rgba(31, 41, 55, 0.37);
            backdrop-filter: blur(6px);
            border-radius: 1.5rem;
            border: 1px solid rgba(34,197,94,0.2);
        }}
        .gradient-bg {{
            background: linear-gradient(135deg, #22c55e 0%, #2563eb 100%);
        }}
        .text-contrast {{ color: #f3f4f6; }}
        .text-contrast-secondary {{ color: #d1d5db; }}
        .input-dark {{
            background-color: #1f2937;
            color: #f3f4f6;
            border: 1px solid #374151;
        }}
        .input-dark::placeholder {{ color: #9ca3af; }}
    </style>
</head>
<body class="gradient-bg min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-3xl font-bold text-contrast">Polls</h1>
            <a href="/logout" class="text-red-400 hover:underline">Logout</a>
        </div>
        <div class="space-y-8">
            {f'<a href="/create-poll" class="btn-green text-white px-4 py-2 rounded-md inline-block">Create Poll</a>' if user['role'] in ["Leader", "Mod"] else ''}
            {polls_html}
            {no_polls}
        </div>
    </div>
</body>
</html>
'''

if __name__ == '__main__':
    # Use only one method to run your app.
    # EITHER run with: python app.py
    # OR run with: flask run (and set FLASK_APP=app.py)
    # Recommended for most users:
    print("Starting app...")
    app.run(host='0.0.0.0', port=5000, debug=True)
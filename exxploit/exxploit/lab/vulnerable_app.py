"""
vulnerable_app.py - Simulated Target for Training Lab
A purposefully vulnerable web application for users to practice exxploit against.
Contains:
- Reflected XSS (Search)
- Stored XSS (Comment Section)
- DOM-based XSS (URL Fragment)
"""

from flask import Flask, request, make_response, render_template_string
import os

app = Flask(__name__)

# Basic template with multiple vulnerability points
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Vulnerable Corp - Training Target</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
        .vuln-box { border: 1px solid #ccc; padding: 1rem; margin: 1rem 0; border-radius: 4px; }
        .vuln-title { font-weight: bold; color: #d9534f; }
        code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
    </style>
</head>
<body>
    <h1>🎯 Training Target</h1>
    <p>Welcome to the exxploit training ground. This application contains several vulnerabilities.</p>

    <!-- Reflected XSS -->
    <div class="vuln-box">
        <div class="vuln-title">1. Search (Reflected XSS)</div>
        <p>Try searching for something...</p>
        <form method="GET" action="/search">
            <input type="text" name="q" placeholder="Enter output...">
            <button type="submit">Search</button>
        </form>
    </div>

    <!-- Stored XSS Simulation -->
    <div class="vuln-box">
        <div class="vuln-title">2. Guestbook (Stored XSS)</div>
        <p>Leave a comment for the admin.</p>
        <form method="POST" action="/comment">
            <textarea name="msg" placeholder="Your message..."></textarea><br>
            <button type="submit">Post</button>
        </form>
        <div id="comments">
            {% for comment in comments %}
                <div class="comment">{{ comment | safe }}</div>
            {% endfor %}
        </div>
    </div>

    <!-- DOM XSS -->
    <div class="vuln-box">
        <div class="vuln-title">3. Hash Handler (DOM XSS)</div>
        <p>The page checks the URL hash for status messages.</p>
        <script>
            // Vulnerable sink
            if (location.hash) {
                document.write("Status: " + decodeURIComponent(location.hash.slice(1)));
            }
        </script>
    </div>
</body>
</html>
"""

# In-memory storage for Stored XSS simulation
COMMENTS = []

@app.route('/')
def home():
    return render_template_string(TEMPLATE, comments=COMMENTS)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    # VULNERABILITY: No escaping of query parameter
    return f"<h1>Search Results for: {query}</h1><a href='/'>Back</a>"

@app.route('/comment', methods=['POST'])
def comment():
    msg = request.form.get('msg', '')
    # VULNERABILITY: Storing raw HTML/JS
    COMMENTS.append(msg)
    return render_template_string(TEMPLATE, comments=COMMENTS)

if __name__ == '__main__':
    host = os.getenv('TARGET_HOST', '0.0.0.0')
    print(f"[*] Starting Vulnerable Target on http://{host}:5000")
    app.run(host=host, port=5000, debug=True)

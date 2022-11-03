import json
import traceback
from flask import redirect, render_template, url_for
from werkzeug.exceptions import HTTPException
from app import app


@app.route("/")
@app.route('/index')
def index():
    return redirect(url_for('data.data')) 


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response
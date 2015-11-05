from flask import Flask
from flask import render_template, request, jsonify
import psycopg2

app = Flask(__name__)

conn = psycopg2.connect(database="asse", user="asse", password="zabalenymotylek2015")
cur = conn.cursor()

@app.route('/')
def homepage():
    return render_template('index.html')

@app.route('/search')
def search():
    return jsonify(result="Couldn't find anything lol")


if __name__ == '__main__':
    app.run(port=8000, debug=True)

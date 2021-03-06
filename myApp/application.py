from flask import Flask, redirect, render_template, request
import sqlite3
import urllib.request
import urllib.parse
import urllib.error
import json
import time
import sys
import os
import codecs

# Configure app
app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/gamePage")
def game():
    return render_template('gamePage.html')


@app.route("/submit-answer", methods=["POST"])
def submitted():
    uname = request.form.get("name")
    answer = request.form.get("answer")
    api_key = os.environ['API_KEY']
    serviceurl = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
    conn = sqlite3.connect('gameData.sqlite')
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS Leaderboard (address TEXT, geodata TEXT, uname TEXT)''')

    parms = dict()
    parms["query"] = answer
    parms["key"] = api_key
    url = serviceurl + urllib.parse.urlencode(parms)
    uh = urllib.request.urlopen(url)
    data = uh.read().decode()
    # json.loads(data)
    cur.execute('''INSERT INTO Leaderboard (address, geodata, uname)
            VALUES ( ?, ?, ? )''', (memoryview(answer.encode()), memoryview(data.encode()), uname))
    conn.commit()
    return render_template('answer-submitted.html')

# dumping the geodata


@app.route("/leaderboard")
def leaderboard():
    conn = sqlite3.connect('gameData.sqlite')
    cur = conn.cursor()
    cur.execute('SELECT * FROM Leaderboard')
    fhand = codecs.open('static/plot.js', 'w', "utf-8")
    fhand.write("myData = [\n")
    count = 0
    for row in cur:
        data = str(row[1].decode())
        try:
            js = json.loads(str(data))
        except:
            continue

        if not('status' in js and js['status'] == 'OK'):
            continue

        lat = js["results"][0]["geometry"]["location"]["lat"]
        lng = js["results"][0]["geometry"]["location"]["lng"]
        if lat == 0 or lng == 0:
            continue
        plot = js['results'][0]['formatted_address']
        plot = plot.replace("'", "")
        try:

            count = count + 1
            if count > 1:
                fhand.write(",\n")
            output = "["+str(lat)+","+str(lng)+", '"+plot+"']"
            fhand.write(output)
        except:
            continue

    fhand.write("\n];\n")
    fhand.close()
    return render_template('plot.html')
    # print(count, "records written to plot.js")
    # print("Open plot.html to view the data in a browser")


if __name__ == '__main__':
    app.run()

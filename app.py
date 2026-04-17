from flask import Flask, render_template, send_from_directory

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signin')
def signin():
    return render_template('signin.html')


@app.route('/static/css/<path:filename>')
def css(filename):
    return send_from_directory('static', filename)


@app.route('/static/js/<path:filename>')
def js(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True)

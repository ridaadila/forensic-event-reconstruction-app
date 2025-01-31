from flask import Flask # type: ignore

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/info')
def info():
    return 'This is a simple Flask web application.'

if __name__ == '__main__':
    app.run(debug=True)
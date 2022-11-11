from flask import Flask,request, url_for, redirect, render_template

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template("landing.html")   

@app.route('/welcome')
def welcomepage():
    return render_template("layout.html")

if __name__ == '__main__':
    app.run(debug=True)
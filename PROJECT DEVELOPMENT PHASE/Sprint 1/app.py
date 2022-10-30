from flask import Flask,request, url_for, redirect, render_template

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template("temp.html")   

@app.route('/done',methods=['POST'])
def donePage():
    userName=request.form.get('userName')

    password=request.form.get('passName')
    return render_template("done.html", userName=userName, password=password)


@app.route('/signUp')
def signUpPage():
    return render_template("signUp.html")


if __name__ == '__main__':
    app.run(debug=True)
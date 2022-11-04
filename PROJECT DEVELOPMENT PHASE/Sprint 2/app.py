from flask import Flask, render_template, request, redirect, url_for, session, flash
import connection
from flask_toastr import Toastr


app = Flask(__name__)

toastr = Toastr(app)

app.secret_key = "ibm_team_cloud"

@app.route('/')
def homepage():
    return render_template("landing.html")   

@app.route('/welcome')
def welcomepage():
    return render_template("layout.html")

@app.route('/question', methods=['GET', 'POST'])
def question():
    if request.method == 'POST':
        money = request.form.get('pmoney')
        budget = request.form.get('dbudget')
        goal = request.form.get('mgoal')
        useremail = session.get('usermail',None)
        pswd = session.get('pwd',None)
        print(useremail,pswd)
        conn = connection.establish()
        connection.setuser(conn,money,budget,goal,useremail,pswd)
        flash('Details added successfully', 'success')
        return redirect(url_for('welcomepage'))
    else:
        return render_template('questionnare.html')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # if 'logged_in' in session and session['logged_in'] == True:
    #     flash('You are already logged in', 'info')
    #     return redirect(url_for('layout.html'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        passw = request.form.get('psw')
        rep_pass = request.form.get('psw-repeat')
        if(passw != rep_pass):
            flash('Confirm password doesnot match','error')
            return redirect(url_for('signup'))
        else:
            conn = connection.establish()
        if(connection.useremail_check(conn,email)==False):
            flash('User with email already exists, try again', 'warning')
            return redirect(url_for('signup'))
        else:
            session['usermail'] = email
            session['pwd'] = passw
            connection.insertuser(conn,name,email,username,passw)
            flash('You are now registered', 'success')
            return redirect(url_for('question'))
    else:
        return render_template('register.html')

#
# class LoginForm(Form):
#     username = StringField('Username', [validators.Length(min=4, max=100)])
#     password = PasswordField('Password', [
#         validators.DataRequired(),
#     ])


@app.route('/login', methods=['GET', 'POST'])
def login():
    # if 'logged_in' in session and session['logged_in'] == True:
    #     flash('You are already logged in', 'info')
    #     return redirect(url_for('addTransactions'))

    if request.method == 'POST' :
        email = request.form.get('email')
        password_input = request.form.get('psw')
        conn = connection.establish()
        if(connection.user_check(conn,email,password_input)==True):
            print('Login Success')
            flash('Login Successfull','success')
            return redirect(url_for('welcomepage'))
        else:
            print('Login Failure')
            flash('Incorrect Username/Password','error')
            return redirect(url_for('login'))
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    flash('You are now logged out', 'success')
    return redirect(url_for('homepage'))


if __name__ == '__main__':
    app.run(debug=True)
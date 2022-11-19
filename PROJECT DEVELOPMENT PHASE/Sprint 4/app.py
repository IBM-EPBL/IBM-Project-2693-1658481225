
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
import plotly.graph_objects as go
from wtforms import Form, PasswordField, IntegerField, StringField, validators
from wtforms.validators import DataRequired
import connection
from wtforms.fields.html5 import EmailField
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_mail import Mail, Message
from flask_toastr import Toastr
import os
from dotenv import find_dotenv,load_dotenv
import ssl
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
ssl._create_default_https_context = ssl._create_unverified_context


app = Flask(__name__)
toastr = Toastr(app)
app.secret_key = "ibm_team_cloud"

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

API = os.getenv("APIKEY")
from_email = os.getenv("FROM")


def sendEmail(API,from_email,to,subject,html):
    if API!=None and from_email!=None and len(to)>0:
        message = Mail(from_email,to,subject,html)
        try:
            sg = SendGridAPIClient(API)
            response = sg.send(message)
            print(response.status_code)
        except Exception as e:
            print(e.message)


@app.route('/')
def homepage():
    return render_template("landing.html")   


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
        return redirect(url_for('addTransactions'))
    else:
        return render_template('questionnare.html')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'logged_in' in session and session['logged_in'] == True:
        flash('You are already logged in', 'info')
        return redirect(url_for('addTransactions'))
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



@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session and session['logged_in'] == True:
        flash('You are already logged in', 'info')
        return redirect(url_for('addTransactions'))

    if request.method == 'POST' :
        email = request.form.get('email')
        password_input = request.form.get('psw')
        conn = connection.establish()
        res = connection.user_check(conn,email,password_input)
        if(res!=False):
            print('Login Success')
            session['logged_in'] = True
            session['usermail'] = email
            session['userID'] = res['ID']
            flash('Login Successfull','success')
            return redirect(url_for('addTransactions'))
        else:
            print('Login Failure')
            flash('Incorrect Username/Password','error')
            return redirect(url_for('login'))
    else:
        return render_template('login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Please login', 'info')
            return redirect(url_for('login'))
    return wrap

@app.route('/profile')
def profile():
    conn = connection.establish()
    res = connection.get_userdetails(conn,session['userID'])
    res2 = connection.gettotalsum(conn, session['userID'])
    total = res2['SUM']
    return render_template('profile.html',
                           name=res['NAME'],
                           email=res['EMAIL'],
                           username=res['USERNAME'],
                           pmoney=res['POCKETMONEY'],
                           dmoney=res['BUDGET'],
                           savings=res['MONTHLYGOAL'],
                           balance=int(res['POCKETMONEY'])-total)


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


@app.route('/addTransactions', methods=['GET', 'POST'])
def addTransactions():
    if request.method == 'POST':
        amount = request.form['amount']
        description = request.form['description']
        category = request.form['category']
        conn = connection.establish()
        connection.inserttransac(conn,session['userID'],amount,description,category)
        flash('Transaction Successfully Recorded', 'success')
        return redirect(url_for('addTransactions'))
    else:
        conn = connection.establish()
        res = connection.gettotalsum(conn,session['userID'])
        total = res['SUM']
        budget = connection.get_budget(conn,session['userID'])
        goal = connection.get_savings(conn,session['userID'])
        if total!=None and total>int(budget['POCKETMONEY']):
            subject = "Exceeded Montly Budget"
            html_content = "You have exceeded your monthly budget, do not spend any more money this month!"
            sendEmail(API,from_email,session.get('usermail'),subject,html_content)
        elif total!=None and int(budget['POCKETMONEY'])-total<int(goal['MONTHLYGOAL']):
            subject = "Savings Goal Affected"
            html_content = "You cannot achieve the target savings goal for the month as you have exceeded your expenses. Try spending carefully next time!"
            sendEmail(API, from_email, session.get('usermail'), subject, html_content)
        elif total!=None and int(budget['POCKETMONEY'])-total<=200:
            subject = "About to exceed your Monthly Budget"
            html_content = "Use your money carefully as you have only '{}' Rs remaining from your monthly budget".format(budget-total)
            sendEmail(API, from_email, session.get('usermail'), subject, html_content)
        dict= connection.getalltransac(conn,session['userID'])
        if len(dict)!=0:
            return render_template('addTransactions.html', totalExpenses=total, transactions=dict)
        else:
            return render_template('addTransactions.html', result=dict)
    return render_template('addTransactions.html')


class TransactionForm(Form):
    amount = IntegerField('Amount', validators=[DataRequired()])
    description = StringField('Description', [validators.Length(min=1)])


@app.route('/editCurrentMonthTransaction/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def editCurrentMonthTransaction(id):
    form = TransactionForm(request.form)
    form = TransactionForm(request.form)

    if request.method == 'POST' and form.validate():
        amount = request.form['amount']
        description = request.form['description']
        conn = connection.establish()
        connection.updateTrans(conn,id,amount,description)
        flash('Transaction Updated', 'success')
        return redirect(url_for('addTransactions'))
    return render_template('editTransaction.html', form=form)

@app.route('/category')
def createBarCharts():
    conn = connection.establish()
    res = connection.gettotalsum(conn, session['userID'])
    total = res['SUM']
    dict = connection.getalltransac(conn, session['userID'])
    if len(dict) > 0:
        values = []
        labels = []
        print(dict)
        for transaction in dict:
            values.append(transaction['amt'])
            labels.append(transaction['cat'])
        print(labels)
        print(values)
        fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
        fig.update_traces(textinfo='label+value', hoverinfo='percent')
        fig.update_layout(title_text='Category Wise Pie Chart For Current Year')
        #fig.show()
    return render_template('chart.html',context={'labels':labels,'value':values})

@app.route('/monthly_bar')
def monthlyBar():
    conn = connection.establish()
    res = connection.gettotalsum(conn, session['userID'])
    total = res['SUM']
    dict = connection.getalltransac(conn, session['userID'])
    if len(dict) > 0:
        year = []
        value = []
        print(dict)
    d={'January':0,'February':0,'March':0,'April':0,'May':0,'June':0,'July':0,'August':0,'September':0,'October':0,'November':0,'December':0}

    for transaction in dict:

        d[transaction['date'].strftime("%B")]+=transaction['amt']
    print(d)

    for t,a in d.items():
        year.append(t)
        value.append(a)
    print(year)
    print(value)

    fig = go.Figure([go.Bar(x=year, y=value)])
    fig.update_layout(title_text='Monthly Bar Chart For Current Year')
    #fig.show()
    #cur.close()
    return render_template('chart1.html',context={'labels':year,'value':value})

@app.route('/monthly_savings')
def monthlysave():
    conn = connection.establish()
    res = connection.gettotalsum(conn, session['userID'])
    total = res['SUM']
    dict = connection.getalltransac(conn, session['userID'])
    r = connection.get_budget(conn, session['userID'])
    print(r)
    if len(dict) > 0:
        year = []
        value = []
        print(dict)
    d={'January':0,'February':0,'March':0,'April':0,'May':0,'June':0,'July':0,'August':0,'September':0,'October':0,'November':0,'December':0}

    for transaction in dict:
        d[transaction['date'].strftime("%B")]+=transaction['amt']
    print(d)

    for t,a in d.items():

          x=int(r['POCKETMONEY'])-a
          if x<0:
              x=0
          year.append(t)
          value.append(x)

    print(year)
    print(value)

    fig = go.Figure([go.Bar(x=year, y=value)])
    fig.update_layout(title_text='Monthly Savings Chart For Current Year')
    #fig.show()
    #cur.close()
    #return redirect(url_for('addTransactions'))

    return render_template('chart2.html',context={'labels':year,'value':value})

class RequestResetForm(Form):
    email = EmailField('Email address', [validators.DataRequired(), validators.Email()])

@app.route("/reset_request", methods=['GET', 'POST'])
def reset_request():
    if 'logged_in' in session and session['logged_in'] == True:
        flash('You are already logged in', 'info')
        return redirect(url_for('index'))
    form = RequestResetForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data
        conn = connection.establish()
        res = connection.get_useralld(conn,email)
        if res == False:
            flash('There is no account with that email. You must register first.', 'warning')
            return redirect(url_for('signup'))
        else:
            user_id = res['ID']
            user_email = res['EMAIL']
            s = Serializer(app.secret_key, 1800)
            token = s.dumps({'user_id': user_id}).decode('utf-8')
            sub = 'Password Reset Request'
            html_content = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make password reset request then simply ignore this email and no changes will be made.
Note:This link is valid only for 30 mins from the time you requested a password change request.
'''
            sendEmail(API,'dragodark223@gmail.com', user_email, sub, html_content)
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('login'))
    return render_template('reset_request.html', form=form)


class ResetPasswordForm(Form):
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if 'logged_in' in session and session['logged_in'] == True:
        flash('You are already logged in', 'info')
        return redirect(url_for('index'))
    s = Serializer(app.secret_key)
    try:
        user_id = s.loads(token)['user_id']
    except:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))

    form = ResetPasswordForm(request.form)
    if request.method == 'POST' and form.validate():
        password = str(form.password.data)
        conn = connection.establish()
        connection.reset_pass(conn,password,user_id)
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


if __name__ == '__main__':
    app.run(debug=True)
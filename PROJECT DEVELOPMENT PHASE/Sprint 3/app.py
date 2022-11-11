
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
import plotly.graph_objects as go
from wtforms import Form, IntegerField, StringField, validators
from wtforms.validators import DataRequired

import connection
from flask_toastr import Toastr


app = Flask(__name__)

toastr = Toastr(app)

app.secret_key = "ibm_team_cloud"

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



if __name__ == '__main__':
    app.run(debug=True)
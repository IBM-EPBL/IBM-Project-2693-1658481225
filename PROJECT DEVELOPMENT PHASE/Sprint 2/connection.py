import ibm_db as db

dbname = "bludb"
hostname = "3883e7e4-18f5-4afe-be8c-fa31c41761d2.bs2io90l08kqb1od8lcg.databases.appdomain.cloud"
port = 31498
protocol = "TCPIP"
username = "jym89748"
password = "8fXXBe0fBoZmJKgG"
cert = "DigiCertGlobalRootCA.crt"

# establish connection
def establish():
    try:
        conn = db.connect(
            f"DATABASE={dbname};HOSTNAME={hostname};PORT={port};PROTOCOL={protocol};UID={username};PWD={password}; SECURITY=SSL; SSLServerCertificate={cert};",
            "", "")
        print("Connected to database")
        return conn
    except:
        print("Error connecting to database")

# to insert a new user
def insertuser(conn1, name, email, user, passw):
    sql = "INSERT INTO users(name,email,username,password) VALUES ('{}','{}','{}','{}')".format(name, email, user, passw)
    try:
        stmt = db.exec_immediate(conn1, sql)
        print("Number of affected rows: ", db.num_rows(stmt))
    except:
        print("cannot insert user to database")

# to check if user exists with given email
def useremail_check(conn,email):
    sql = "SELECT * FROM users WHERE email='{}' ".format(email)
    stmt = db.exec_immediate(conn, sql)
    results = db.fetch_assoc(stmt)
    if results == False:
        return True
    else: return False

# to check if user exists with given username and password
def user_check(conn,email,passw):
    sql = "SELECT * FROM users WHERE email='{}' AND password='{}'".format(email,passw)
    stmt = db.exec_immediate(conn, sql)
    results = db.fetch_assoc(stmt)
    if results == False:
        return False
    else: return True

def setuser(conn,money,budget,goal,email,pwd):
    sql = "UPDATE USERS SET(pocketmoney,budget,monthlygoal) = ('{}','{}','{}') WHERE email='{}' AND password='{}'".format(money,budget,goal,email,pwd)
    try:
        stmt = db.exec_immediate(conn,sql)
        print("Number of affected rows: ", db.num_rows(stmt))
    except:
        print("Error inserting data to database")
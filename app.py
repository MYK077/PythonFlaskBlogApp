
from flask import Flask,render_template,redirect,url_for,session,logging,request,flash
# importing article function from articles
from articles import Articles

from flask_mysqldb import MySQL

from wtforms import Form, StringField, TextAreaField, PasswordField, validators

from passlib.hash import sha256_crypt

# creating instance of class Flask
app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'myflaskapp'
# by default cursor class return objects as tuple,
# so if you want to return data from db in dictionary format set MYSQL_CURSORCLASS to 'DictCursor'
app.config['MYSQL_CURSORCLASS']= 'DictCursor'

# init MySQL
mysql = MySQL(app)

Articles = Articles()

# Index
@app.route("/")
def index():
    return render_template("home.html")

# About
@app.route("/about")
def about():
    return render_template("about.html")

# article
@app.route("/articles")
def articles():
    return render_template("articles.html",articles = Articles)

#Single Article
@app.route("/article/<string:id>")
def article(id):
    return render_template("article.html",id = id)

# Register form class
# http://flask.pocoo.org/docs/1.0/patterns/wtforms/
class RegistrationForm(Form):
    name = StringField('Name', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')

# Username Register
# http://flask.pocoo.org/docs/1.0/patterns/wtforms/
@app.route('/register', methods=['GET', 'POST'])
def register():
    # The request.form command is used to collect values in a form with method="post"
    # request.form: the key/value pairs in the body, from a HTML post form
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        name =form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        # create cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password)VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()
        # Close connection
        cur.close();
        flash('Thanks for registering','success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        # create cursor
        cur = mysql.connection.cursor()
        result= cur.execute("SELECT * FROM users WHERE username = %s",[username])
        if result > 0:
            data = cur.fetchone()
            password = data['password']
            if sha256_crypt.verify(password_candidate,password):
                app.logger.info('Password Matched')
                session['logged_in'] = True
                session['username'] = username
                flash("you are now logged in","success")
                return redirect(url_for('dashboard'))
            else:
                app.logger.info('Invalid Password')
                error = "Invalid password"
                return render_template('login.html',error = error)
            # close Connection
            cur.close()

        else:
            flash('user not found','danger')
            # error = "user not found"
            return render_template('login.html')
    else:
        return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('you are logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        cur = mysql.connection.cursor();
        res = cur.execute("select * from articles")
        articles = cur.fetchall()
        if res > 0:
                return render_template('dashboard.html', articles = articles)
        return render_template('dashboard.html',username = session['username'])
    else:
        flash('unauthorized,please log in','danger')
        return redirect(url_for('login'))

# adding wtf form class to add article:
class AddArticle(Form):
    # author = StringField('AuthorName', [validators.Length(min=4, max=100)])
    title = StringField('Article Title', [validators.Length(min=6, max=100)])
    body = TextAreaField('Content', [validators.DataRequired(),validators.Length(min=30)])


@app.route('/addarticle', methods=['GET','POST'])
def addarticle():
    form = AddArticle(request.form)
    # author = session['username']
    if request.method == "POST" and form.validate():
        title = form.title.data
        body = form.body.data
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO articles(author, title, body)VALUES(%s, %s, %s)", (session['username'],title,body))
        mysql.connection.commit()
        cur.close()
        flash("Article created","success")
        return redirect(url_for("dashboard"))
    return render_template('addarticle.html',form=form)


    # if 'username' in session:
    #     return render_template('dashboard.html',username = session['username'])
    # else:
    #     flash('unauthorized,please log in','danger')
    #     return redirect(url_for('login'))

# @app.route('/')
# def users():
#     cur = mysql.connection.cursor()
#     name =
#     cur.execute('''SELECT user, host FROM mysql.user''')
#     rv = cur.fetchall()
#     return str(rv)

if __name__ == '__main__':
    app.secret_key = "secret123"
    # run is a Flask method to run the application
    # debug = True (if you make any changes in your code,
    # you dont really have to restart the server )
    # Note: the website was extremely slow earlier so I added threaded = true. it works faster somehow
    app.run(debug=True,threaded=True)

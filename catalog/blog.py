#!/usr/bin/env python3
# Import postgresql

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask import jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, User, Post


# New imports for this step
from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Blog Application"

engine = create_engine('sqlite:///blog.db',
                       connect_args={'check_same_thread': False}, echo=True)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# ******************** Create anti-forgery state token***********************
@app.route('/')
@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# ***********************Google Login**************************************


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
        access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)
    login_session['username'] = data["name"]
    login_session['picture'] = data["picture"]
    login_session['email'] = data["email"]

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1 style="text-align:center; margin-top:50px;">'
    'Login Successful!!</h1>'
    output += '<h1 style="text-align:center">Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "margin-left:500px; margin-top:10px; width: 300px;'
    ' height: 300px;border-radius: 150px;-webkit-border-radius: 150px;'
    '-moz-border-radius: 150px;"> '
    output += '<p style="text-align:center;margin-top:50px">Redirecting...</P>'
    print("done!")
    return output

# ******************* Google Disconnect ************************


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user Disconnected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['email'])
    url = 'https://accounts.google.com/o/oauth2/'
    'revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('showLogin'))
    else:
        response = make_response(json.dumps('Failed to revoke'
                                            ' token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# ***********************************JSON*********************************

@app.route('/posts/JSON/')
def postsJSON(news_id):
    posts = session.query(Post).filter_by(news_id).all()
    return jsonify(posts=[i.serialize for i in posts])


# *******************************  POSTS  **************************

@app.route('/')
@app.route('/posts/')
def showPosts():
    allposts = session.query(Post)
    uname = ''
    pic = ''
    if 'username' in login_session:
        uname = login_session['username']
        pic = login_session['picture']
        return render_template(
            'home.html',
            allposts=allposts,
            name=uname,
            picture=pic)
    else:
        return render_template(
            'home.html',
            allposts=allposts,
            name=uname,
            picture=pic)

# ***************************** To Create a New Post ************************


@app.route('/posts/new/', methods=['GET', 'POST'])
def newPosts():
    if 'username' not in login_session:
        return redirect('/login')
    if 'username' in login_session:
        if request.method == 'POST':
            newpost = Post(
                name=request.form['name'],
                user_id=login_session['user_id'],
                post_type=request.form['post_type'],
                description=request.form['description'],
                image=request.form['image'],
                ratings=request.form['ratings'])
            session.add(newpost)
            flash("New Post Created Successfully")
            session.commit()
            return redirect(url_for('showPosts'))
        else:
            return render_template('newPost.html')

# ***************************** To Edit Posts ************************


@app.route('/posts/<int:post_id>/edit/', methods=['GET', 'POST'])
def editPosts(post_id):
    if 'username' not in login_session:
        return redirect('/login')
    if 'username' in login_session:
        editedpost = session.query(Post).filter_by(id=post_id).one()
        if request.method == 'POST':
            if request.form['name']:
                editedpost.name = request.form['name']
            if request.form['description']:
                editedpost.description = request.form['description']
            if request.form['post_type']:
                editedpost.post_type = request.form['post_type']
            session.add(editedpost)
            session.commit()
            flash("Post Edited Successfully")
            return redirect(url_for('showPosts'))
        else:
            return render_template('editpost.html',
                                   post_id=post_id,
                                   post_name=editedpost)

# *************************** To Delete the posts ********************


@app.route('/posts/<int:post_id>/delete/', methods=['GET', 'POST'])
def deletePosts(post_id):
    if 'username' not in login_session:
        return redirect('/login')
    if 'username' in login_session:
        deletepost = session.query(Post).filter_by(id=post_id).one()
        if request.method == 'POST':
            session.delete(deletepost)
            session.commit()
            flash("Post Deleted Successfully")
            return redirect(url_for('showPosts'))
        else:
            return render_template('deletepost.html',
                                   post_id=post_id,
                                   post_name=deletepost)

# *********************************Show Post********************************


@app.route('/posts/<int:post_id>/')
def fullPosts(post_id):
    fullpost = session.query(Post).filter_by(id=post_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    user_id = getUserID(login_session['email'])
    return render_template('post.html', fullpost=fullpost, user_id=user_id)
    # else:
    #     return render_template('publicpost.html', fullpost=fullpost)

# *************** It displays the home page of the posts list **************


@app.route('/posts')
def homePosts():
    posts = session.query(Post).filter_by(post_type='Home').all()
    if 'username' in login_session:
        uname = login_session['username']
        pic = login_session['picture']
        return render_template('home.html',
                               allposts=posts, name=uname, picture=pic)
    else:
        return render_template('home.html',
                               allposts=posts)

# ******************** It displays the Popular Posts ********************


@app.route('/posts/popular')
def popPosts():
    posts = session.query(Post).filter_by(post_type='Popular').all()
    if 'username' in login_session:
        uname = login_session['username']
        pic = login_session['picture']
        return render_template('home.html',
                               allposts=posts, name=uname, picture=pic)
    else:
        return render_template('home.html',
                               allposts=posts)

# ******************* It displays the Technical Posts *******************


@app.route('/posts/technical')
def techPosts():
    posts = session.query(Post).filter_by(post_type='Technical').all()
    if 'username' in login_session:
        uname = login_session['username']
        pic = login_session['picture']
        return render_template('home.html',
                               allposts=posts, name=uname, picture=pic)
    else:
        return render_template('home.html',
                               allposts=posts)

# *************** Displays the Entertainment type of Posts **************


@app.route('/posts/entertainment')
def entPosts():
    posts = session.query(Post).filter_by(post_type='Entertainment').all()
    if 'username' in login_session:
        uname = login_session['username']
        pic = login_session['picture']
        return render_template('home.html',
                               allposts=posts, name=uname, picture=pic)
    else:
        return render_template('home.html',
                               allposts=posts, name=uname, picture=pic)

# ************** Displays the Sports type of Posts ******************


@app.route('/posts/sports')
def spoPosts():
    posts = session.query(Post).filter_by(post_type='Sports').all()
    if 'username' in login_session:
        uname = login_session['username']
        pic = login_session['picture']
        return render_template('home.html',
                               allposts=posts, name=uname, picture=pic)
    else:
        return render_template('home.html',
                               allposts=posts, name=uname, picture=pic)


# ****************************** User ************************************

def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        return None


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)

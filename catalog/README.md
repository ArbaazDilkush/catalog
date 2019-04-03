#### Item Catalog 
This is a project for the Udacity FSND Course.

### About
This project is a website based that allows users to see the existing posts lists. Where, user can find day to day updated posts. User can get the categories of Sports, Technical, Popular, Entertainment. Depending upon the flow of particular post the ratings can be given for each and every post. User should login with his/her Google Gmail account for posts list.

User cannot have an option to update and delete the existing posts. The entered user can create and he can do operations of update and delete of his/her created posts only.  

### In This Repo
This project has one main Python file named as project.py which runs the flask application. A SQL database is created using the database_setup.py module. The Flask application uses stored HTML templates in the tempaltes folder to build the front-end of the application.

### Skills 
Python
HTML
CSS
OAuth
Flask Framework
SQLAlchemy

### Installation
There are some dependancies and a few instructions on how to run the application.

### Dependencies
Vagrant
Udacity Vagrantfile
VirtualBox

### How to Install
Install VirtualBox
Install Vagrant
Clone the Udacity Vagrantfile

Launch the Vagrant VM:  (vagrant up)
Log into Vagrant VM:  (vagrant ssh)
After log into vagrant type command: cd/vagrant 
First we have to run the database;
Setup application database python database_setup.py
Now we have to run the main project;
Run application using python project.py
Access the application locally using http://localhost:8000



### Using Google Login
To get the Google login working there are a few additional steps:

Go to Google Dev Console
Sign up or Login if prompted
Go to Credentials
Select Create Crendentials > OAuth Client ID
Select Web application
Enter name 'catalog' or 'posts'(as user's wish)
Authorized JavaScript origins = 'http://localhost:8000'
Authorized redirect URIs = 'http://localhost:8000/login' && 'http://localhost:8000/gconnect'
Then click on Create
Copy the Client ID and paste it into the data-clientid in login.html/ any need of clientid
On the Dev Console Select Download JSON
Rename JSON file to client_secrets.json
Place JSON file in item-catalog directory that you cloned from here
Run application using python project.py


### URL's of my project

http://localhost:8000
Sign in to Gmail account
If login success.... Then,
It redirects to http://localhost:8000/posts


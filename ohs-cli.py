# This is a Python script for managing your database. This is primarily for diagnostics, especially once the WebUI is fleshed out
from os import system, name, listdir
import sys, webbrowser, sqlite3, time, datetime, hashlib, secrets

# all of the '\033[0;31mOHS \033[0m> ' is formatting the text to red and back for the coolness factor

version = "0.0.1-β"

def cls():
    if name == 'nt': #windows
        system('cls')
    else: # nix
        system('clear')

helpPrintout = """
Open Health Software, Version %s.

Syntax: ohs-cli.py [ARGUMENT]

If you are following through development, please keep in mind these commands can and will change with time.

Arguments include:
    - createdb          create a new databse file
    - exit              exit program
    - dbinfo            return information about your existing database
    - deletedb          delete a database file
    - help              print this page
    - import FILE       import an appropriate file
    - login (USER)      log into a user profile
    - user (USER)       manage a user's data
    - web [UP|DOWN]     start or stop the WebUI
    - wiki              open the wiki page on GitHub

For a further explanation on any of the commands, please see the wiki page.
"""

def initDB():
    con = sqlite3.connect("config/ohs.sqlite")
    cur = con.cursor()
    print('Creating DB...')
    cur.execute("CREATE TABLE ohs(title, version, init_date)")
    cur.execute("INSERT INTO ohs VALUES ('ohs', '1', '"+str(time.time())+"')") # inserts name, version number and unix timestamp
    con.commit()
    con.close()
    usrcon = sqlite3.connect("config/users.sqlite")
    usrcur = usrcon.cursor()
    usrcur.execute("CREATE TABLE users(user_id, name, salt, password_hash)")
    usrcon.commit()
    usrcon.close()
    print('Done!')
    choice = input('We recommend creating a user after generating a new database. Would you like to do this now? [y/N] ') # maybe make y default?
    if choice.lower() == 'y':
        newUser()
    else: print('Skipping user creation. You can always make one later by inciting "user".')

def newUser():
    # look into this to avoid echoing pw    https://docs.python.org/3/library/getpass.html
    # also i should hash the passwords before saving them to variables. probably.
    # at the end of the day, this is a privately-hosted tool, how secure do passwords need to be?
    # genuinely asking.
    print('Hello, welcome to OHS. Lets set up a profile.')
    userID = len(usrcur.execute('SELECT name FROM users').fetchall()) + 1 # this is a list of all users in the 'users' table
    newName = input('\033[0;31mName \033[0m> ').lower() # everything gets fucked when we make case-sensitive names!
    # TODO: PREVENT USER FROM CLAIMING EXISTING NAME
    newPass = (input('\033[0;31mPassword \033[0m> '))
    newPas2 = input('\033[0;31mConfirm Password \033[0m> ')
    if newPass != newPas2:
        print('Password mismatch. Restarting process...') 
        newUser()
    hashPass = hashlib.sha256(bytes(newPass, encoding="utf8")).hexdigest() # generates a hash of the provided password. required to specify type bytes and the encoding.
    salt = str(secrets.randbits(256)) # generate a salt pattern
    hashSalt = hashlib.sha256(bytes(salt+hashPass, encoding="utf8")).hexdigest() # hash the salt alongside the hashed password for a salted password
    fill = ("INSERT INTO users VALUES ('{}','{}','{}','{}')").format(userID, newName, salt, hashSalt) # this seems like the best way to feed all the variables into sqlite
    #print(fill)
    usrcur.execute(fill)
    usrcon.commit()

def login(): # NOT FINISHED
    usrlist = usrcur.execute('SELECT name FROM users').fetchall()
    
    user = input('\033[0;31mUsername \033[0m> ').lower()
    if user not in (str(u).split("'")[1].lower() for u in usrlist): # case insensitivity. also need to remove the (''), from the table
        print('User "%s" does not exist'%user)
        prompt() #if fail return to initial prompt
    password = input('\033[0;31mPassword \033[0m> ')
    passwordHashed = hashlib.sha256(bytes(password, encoding="utf8")).hexdigest()
    tmpSalt = str(usrcur.execute('SELECT salt FROM users WHERE name=\'%s\''%user).fetchall()[0]).split("'")[1]
    tmpPass = str(usrcur.execute('SELECT password_hash FROM users WHERE name=\'%s\''%user).fetchall()[0]).split("'")[1]
    tmpHash = hashlib.sha256(bytes(tmpSalt+passwordHashed, encoding="utf8")).hexdigest() # re-hashing and re-salting, should match password_hash in SQL table
    if tmpPass == tmpHash:
        print('Login sucess!')
    else:
        print('Login failed')



def userManager():
    try:
        usrlist = usrcur.execute('SELECT name FROM users').fetchall() # grab all users from users table
    except: # this exception will stop the program from crashing if there is somehow a ohs table but no users table (99% chance file tampered externally)
        usrcur.execute("CREATE TABLE users(user_id, name, salt, password_hash)")
        usrlist = usrcur.execute('SELECT name FROM users').fetchall()
    if usrlist  == []:
        choice = input('It looks like there isn\'t yet a user set up. Would you like to do that now? [Y/n] ')
        if choice.lower() != 'n':
            newUser()
    else:
        print('Available users:')
        for i in usrlist:
            print(' - ', str(i).split("'")[1]) # print all users in table. gets rid of the (''), parts
    
    
def prompt(): # prompting the user for their own input. kind of like its own shell, in the same way sqlite or python have nested shells. (if thats the right terminology)
    strIn = input('\033[0;31mOHS \033[0m> ')

    if strIn == 'clear':
        cls()
    elif strIn == 'dbinfo': # maybe short functions like this should still be dedicated functions for readability's sake
        dbVer, dbDate = cur.execute("SELECT version, init_date FROM ohs").fetchone()
        print(f'Your database is on version {dbVer}, dated', datetime.datetime.utcfromtimestamp(float(dbDate.split('.')[0])))
    elif strIn == 'exit':
        exit()
    elif strIn == 'login':
        login()
    elif strIn == 'newuser':
        newUser()
    elif strIn == 'help':
        print(helpPrintout%version)
    elif strIn == 'user':
        userManager()
    elif strIn == 'wiki':
        print('Opening webpage...')
        webbrowser.open('https://github.com/shawnshyguy/OpenHealthService/wiki')
    else: print('Command "'+str(strIn)+'" not found. Try "help" for available commands.')
    prompt()

#------------
# program actually starts running here. everything beforehand is fuckin functions lol
#------------
cls()
print('OHS Ver %s'%version)
if 'ohs.sqlite' not in listdir('config'): # check on startup for a database. this only checks for an ohs db, does not confirm a users one. while its unlikely one would exist without the other, it probably still should be checking for that stuff.
    input('It appears you do not have a database file. Please press enter to create one now.')
    initDB()

# initializing both sqlite libraries now to avoid repeated lines in a bunch of dirs.
con = sqlite3.connect("config/ohs.sqlite")
cur = con.cursor()
usrcon = sqlite3.connect("config/users.sqlite")
usrcur = usrcon.cursor()
prompt()

# maybe i should commit and close both dbs before the script ends, rather than doing so in the functions themselves?
# alternatively i could have a function that checks the status of either DB, and opens/closes them depending on what the current task requires.
# look into this.
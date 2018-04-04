Riki-deploy is the version that is modified to be executed from Ubuntu server. 
You can use PyCharm and command line tools to start the Flask/Wiki system with “python Riki.py”.
You can access the wiki [http://wiki440.ms2ms.com](http://wiki440.ms2ms.com).

## Configuration
    
1. Update CONTENT_DIR and USER_DIR in config.py
2. When you want to use login, make PRIVATE = True in config.py. Remember you can use id "name" and password "1234".

## Process
    
1. create virtualenv name `env` in the Riki-deploy directory.
2. source env/bin/activate
3. pip install -r requirements.txt
4. Modify the location of CONTENT_DIR in config.py. `CONTENT_DIR = '/Users/smcho/PycharmProjects/Riki/content'`
5. Restart the uwsgi - `sudo restart uwsgi` 
6. sudo chown -R www-data:www-data content
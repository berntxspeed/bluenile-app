# bluenile-app

At this point, it is just a simple API CR_D (of CRUD) to a simple key/value db table

But, it uses the Dependency Injection design pattern - decoupling sections of the code

===

To run the program locally:
1. Install mongodb, redis, postgresql, python3, virtualenv, virtualenvwrapper, autoenv
2. Create a new virtual environment:
    mkvirtualenv <your-virtual-env> --python=python3
3. Instantiate database
    psql postgres "create database simple_di_flask_dev"
4. In the root level create a .env file that contains 2 lines
    source config/local.env
    workon <your-virtual-env>
5. Go to the folder:
    cd <folder where this is checked out>
    *make sure you activated your virtualenvironment*
    pip install -r requirements.txt
6. Init database
    ./deploy.sh


YET TO DO: 
*add model/service structure
*incorporate db migration tools
*employ a cohesive client-side dev strategy
*add authentication

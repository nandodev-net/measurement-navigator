# measurement-navigator
Measurement review suite for ooni measurements

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

## About Measurement Navigator

The measurement navigator is a tool to assist the anlisys of OONI network measurements to detect internet Censorship in one specific context

### Important objects and concepts

#### Raw measurement: 
The measurement as obtained from OONI's servers.

#### Sub-measurement:
A more streamlined object with a sub-section of the elements of a measurement made available as attributes. This allows us to display and filter the same info important to a kind of measurement in a table, with faster performance.

Different types of sub-measurements are implemented, some test measurement types can create more than one sub-measurement. 

Sub-measurements can be as simple as a few common attributes and one or two attributes taken from measurement_keys, or something more complex with attributes calculated at the time, depending on what's usually needed for a quick assessment or what attributes are important to filter.

**measurement_name = > sub-measurement type**

Web_connecitivy => DNS, HTTP, TCP
Tor => Tor
Coming soon: DNS => DNS (making the same sub-measurement as web_connecitivy)

### Flag
An asessment on the sub-measurement.

SOFT: Logic in the system determined the measurement is anomalous and could be indicative of censorship. this logic can be different from the one used by OONI to account for local needs or individual fingerprints
HARD: A flag has been repeating over time, requiring immediate attention 
MANUAL: A flag that's been manually flagged by an analyst, not the system

### Event
An event is the semi-continuous range of measurements related to a single internet censorship event.
An event has:
* start date (automatic from measurements or manual)
* end date (automatic from measurements or manual)
* One ISP
* One target
* List of measurements

### Case
A small post collecting context, explanation, events and measurements of a single censorship case, tipically the blocking of one website.
A case has:
* start date (automatic from events or manual)
* end date (automatic from events or manual)
* Multiple ISPs
* Multiple (but tipically one) website (can have events for many urls and domains for the same site)
* Title
* Description

## Instalation.

Not counting the isntallation of a web browser ngnix and a web server gateway such as Gunicorn. These are the steps needed to install this project

1. **Clone the repository**
`git clone https://github.com/VEinteligente/measurement-navigator.git`

2. **Now, from the project root, you must install the requirements.**
`pip install -r requirements.txt`

3. **If you don't have a postgres database for this project, create one:**
`sudo -i -u [ usuario_de_postgres ]`
`psql`
`create database [ nombre_database ]`

4. **Create an env file in the following path and edit it with the access data of the database, for example:**
`
    VSF_DB_NAME=vsf_db
`
`
    VSF_DB_USER=postgres
`
`
    VSF_DB_PASSWORD=change_this_example_password
`
`
    VSF_DB_HOST=localhost
`
`
    VSF_DB_PORT=5432 
`

5. **Create the project datatables in the database**
`python manage.py makemigrations`
`python manage.py migrate`

6. **Create a system administrator user**
`python manage.py create superuser`

7. **Finally, run the server**
`python manage.py runserver`

##
## Requirements of the system:
##
~amqp==2.6.1~
~asgiref==3.2.8~
~attrs==19.3.0~
~autopep8==1.5.3~
~billiard==3.6.3.0~
~celery==4.4.7~
~certifi==2020.4.5.2~
~chardet==3.0.4~
~coreapi==2.3.3~
~coreschema==0.0.4~
~Django==3.0.7~
~django-celery-beat==2.0.0~
~django-celery-results==1.2.1~
~django-ckeditor==6.0.0~
~django-cors-headers==3.7.0~
~django-datatables-view==1.19.1~
~django-environ==0.4.5~
~django-filter==2.3.0~
~django-js-asset==1.2.2~
~django-model-utils==4.0.0~
~django-sass==1.0.0~
~django-timezone-field==4.0~
~django-tinymce==3.3.0~
~django-webpack-loader==0.7.0~
~django-widget-tweaks==1.4.8~
~django-wysiwyg==0.8.0~
~djangorestframework==3.11.0~
~drf-yasg==1.17.1~
~flower==0.9.5~
~gunicorn==20.0.4~
~humanize==2.6.0~
~idna==2.10~
~inflection==0.5.1~
~itypes==1.2.0~
~Jinja2==2.11.2~
~jsonschema==3.2.0~
~kombu==4.6.11~
~libsass==0.20.1~
~Markdown==3.2.2~
~MarkupSafe==1.1.1~
~packaging==20.4~
~prometheus-client==0.8.0~
~psycopg2-binary==2.8.5~
~pycodestyle==2.6.0~
~pyparsing==2.4.7~
~pyrsistent==0.16.0~
~python-crontab==2.5.1~
~python-dateutil==2.8.1~
~pytz==2020.1~
~PyYAML==5.3.1~
~requests==2.24.0~
~ruamel.yaml==0.16.10~
~ruamel.yaml.clib==0.2.0~
~six==1.15.0~~
~sqlparse==0.3.1~
~swagger-spec-validator==2.7.3~
~toml==0.10.1~
~tornado==6.0.4~
~uritemplate==3.0.1~
~urllib3==1.25.9~


## Info for users 

To access the software, you must to introduce your credentials in Measurement Navigator login page. After that, you will see a dashboard with a sidebar which has links to the following sections:

- **Measurements, with the following submodules:**
    -   Measurement List.
    -   DNS Submeasurement List.
    -   HTTP Submeasurement List.
    -   TCP Submeasurement List.
    -   TOR Submeasurement List.
- **Events, module that contains the events list.**
- **Cases, with the subsequents submodules:**
    - Cases List.
    - Create Case.
- **Sites, that contains the submodules:**
    - Domain.
    - Sites.
- **Control Panel, module that contains the global configuration panel.**
- **Users, with:**
    - List Users.
    - New User.

This sidebar contains a menu button ≡, which you can use to minimize or expand the sidebar menu, useful in order to have a wider view.

Another global and useful tool in the software is the header containing a dropdown with an user icon , that allow manage the account configuration, like the account, the admin site and close the session. Also, you will find next to the user dropdown, the time zone dropdown, which changes the time configuration of the dates in the software. Down all that, you can find, The title of the page current contain, a short description and the breadcrumb. 

**Common tools in most sections:**

1. **Filters**
    Across the modules, there are a card at the top of contains that have several inputs. These filters allow reducing the amount of data in the datatable at the user's will. Also, in some badges, you can find a checkbox that enable/disable the capacity of the search engine of search while you are picking/writing the filters or just activate it when the user clicks the search button.
2. **Datatable**
    The datatable is the main visualization tool to analize data in this software, commonly you can double click a row of the datatable and check the details of that row. Also, you can filter by alphabetical order clicking the header of the datatable.



# PulseLabz Dashboard

Dashboard application to view incoming orders, send orders to fulfillment, track shipment and log information to a Google spreadsheet for reporting purposes.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

Python 3 needs to be installed. Get the latest version of Python at https://www.python.org/downloads/ or with your operating system’s package manager. On Windows make sure Python is added to your Environment path: https://www.pythoncentral.io/add-python-to-path-python-is-not-recognized-as-an-internal-or-external-command/

To verify that Python is installed by typing python from your Terminal or Command Prompt; you should see something like:

```
Python 3.x.y
[GCC 4.x] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>>
```

Once Python is installed, you also need to install pip
* Windows: https://www.liquidweb.com/kb/install-pip-windows/
* *nix: curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py

To verify that pip is installed, run the following command:
```
pip --version
```

### Installing

1. Clone this repository using git

2. To easily manage dependencies, it is recommended that you create a virtual environment for this project. Navigate to the repository and run the following:

```
python -m venv env
```
Depending on your system:
* *nix: source env/bin/activate
* Windows: \env\Scripts\activate.bat

3. Install project dependencies
```
pip install -r requirements.txt
```

4. Install Postgresql

Depending on your system:
* *nix: brew install Postgresql && brew services start postgresql
* Windows: https://www.postgresql.org/download/

### Secrets keys

This project relies on secret keys in two files
* pulselabz.json
* secrets.py

Contact the project contributors for access.

### Running the application locally for the first time

```
python manage.py migrate
python manage.py runserver
```

## Deployment

New changes pushed to GitHub are deployed via Heroku.

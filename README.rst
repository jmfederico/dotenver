============================
Python DotEnver
============================

.. image:: https://badge.fury.io/py/dotenver.svg
    :target: https://badge.fury.io/py/dotenver

.. image:: https://github.com/jmfederico/dotenver/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/jmfederico/dotenver/actions/workflows/tests.yml

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black

A Python app to generate dotenv (.env) files from templates.


Features
--------

* Automatic .env file generation from .env.example files
* Useful for CI or Docker deployments
* Uses Jinja2_ as rendering engine
* Uses Faker_ for value generation


Quickstart
----------

1. Install **Python DotEnver**

   .. code-block:: console

    $ pip install dotenver

2. Create a **.env.example** following this example

   .. code-block:: ini

    # Full line comments will be kept

    # Simple usage
    NAME= ## dotenver:first_name

    # Pass parameters to fakers
    ENABLED= ## dotenver:boolean(chance_of_getting_true=50)

    # Name your values
    MYSQL_PASSWORD= ## dotenver:password:my_password(length=20)
    # And get the same value again, when the name is repeated.
    DB_PASSWORD= ## dotenver:password:my_password()

    # Output your values within double or single quotes
    DOUBLE_QUOTED= ## dotenver:last_name(quotes='"')
    SINGLE_QUOTED= ## dotenver:last_name(quotes="'")

    # Literal values are possible
    STATIC_VARIABLE=static value

    # export syntax can be used
    export EXPORTED_VARIABLE=exported

3. Run python **DotEnver** form the CLI

   .. code-block:: console

    $ dotenver -r

4. You now have a new **.env** file ready to use.

5. For more usage options run

   .. code-block:: console

    $ dotenver -h


Docker
------

A Docker image `is provided <Dotenver image_>`_. To use it, mount your source code to
`/var/lib/dotenver/` and run the container.

.. code-block:: console

    $ docker run -ti --rm -v "${PWD}:/var/lib/dotenver/" jmfederico/dotenver

.. _Faker: https://faker.readthedocs.io
.. _Jinja2: http://jinja.pocoo.org
.. _jmfederico: https://github.com/jmfederico
.. _`Dotenver image`: https://hub.docker.com/r/jmfederico/dotenver

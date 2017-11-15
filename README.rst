txBreezeChMS
============

Twisted Python interface to BreezeChMS REST API
http://www.breezechms.com

Based on
`pyBreezeChMS <https://github.com/alexortizrosado/pyBreezeChMS>`__ by
Alex Ortiz-Rosado

Installation
------------

::

    $ pip install txbreezechms

Getting Started
---------------

.. code:: python

    from txbreeze import breeze

    breeze_api = breeze.BreezeApi(
        breeze_url='https://your_subdomain.breezechms.com',
        api_key='YourApiKey')

To get a JSON of all people:

.. code:: python


    people = breeze_api.get_people()
    # people is a Deferred instance

License
-------

Code released under the `Apache
2.0 <https://github.com/aortiz32/pyBreezeChMS/blob/master/LICENSE>`__
license.

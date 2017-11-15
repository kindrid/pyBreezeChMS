"""Unittests for breeze.py

Usage:
  python -m unittest tests.breeze_test
"""

import json

from twisted.internet import defer
from twisted.python.failure import Failure
from twisted.trial import unittest
from twisted.web.client import ResponseDone
from twisted.web.http_headers import Headers

from txbreeze import breeze


class MockConnection(object):
    """Mock requests connection."""

    def __init__(self, response):
        self._url = None
        self._params = None
        self._headers = None
        self._response = response

    def post(self, url, params, headers, timeout):
        self._url = url
        self._params = params
        self._headers = headers
        return self._response

    @property
    def url(self):
        return self._url

    @property
    def params(self):
        return self._params


class MockResponse(object):
    """ Mock requests HTTP response."""

    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content
        self.headers = Headers()

    @property
    def ok(self):
        return str(self.status_code).startswith('2')

    @property
    def length(self):
        return len(self.content)

    def json(self):
        if self.content:
            return json.loads(self.content)
        return None

    def raise_for_status(self):
        raise Exception('Fake HTTP Error')

    def deliverBody(self, protocol):
        protocol.dataReceived(self.content)
        protocol.connectionLost(Failure(ResponseDone()))


FAKE_API_KEY = 'fak3ap1k3y'
FAKE_SUBDOMAIN = 'https://demo.breezechms.com'


class BreezeApiTestCase(unittest.TestCase):
    """Test the Breeze API wrapper"""

    def test_invalid_subdomain(self):
        """Test valid and invalid subdomains"""
        self.assertRaises(breeze.BreezeError, lambda: breeze.BreezeApi(
            api_key=FAKE_API_KEY,
            breeze_url='invalid-subdomain'))
        self.assertRaises(breeze.BreezeError, lambda: breeze.BreezeApi(
            api_key=FAKE_API_KEY,
            breeze_url='http://blah.breezechms.com'))
        self.assertRaises(breeze.BreezeError,
                          lambda: breeze.BreezeApi(api_key=FAKE_API_KEY,
                                                   breeze_url=''))

    def test_missing_api_key(self):
        self.assertRaises(
            breeze.BreezeError,
            lambda: breeze.BreezeApi(api_key=None,
                                     breeze_url=FAKE_SUBDOMAIN))
        self.assertRaises(
            breeze.BreezeError,
            lambda: breeze.BreezeApi(api_key='',
                                     breeze_url=FAKE_SUBDOMAIN))

    @defer.inlineCallbacks
    def test_get_people(self):
        response = MockResponse(200, json.dumps({'name': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        breeze_api.get_people(limit=1, offset=1, details=True)
        self.assertEquals(
            connection.url,
            '{}{}'.format(FAKE_SUBDOMAIN, breeze.ENDPOINTS.PEOPLE)
        )
        self.assertEqual(connection.params, {"limit": 1, "offset": 1, "details": 1})
        res = yield breeze_api.get_people()
        self.assertEqual(res, json.loads(response.content))

    @defer.inlineCallbacks
    def test_get_profile_fields(self):
        response = MockResponse(200, json.dumps({'name': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        res = yield breeze_api.get_profile_fields()
        self.assertEqual(res, json.loads(response.content))

    @defer.inlineCallbacks
    def test_get_person_details(self):
        response = MockResponse(200, json.dumps({'person_id': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        person_id = '123456'
        res = yield breeze_api.get_person_details(person_id)
        self.assertEquals(
            connection.url, '%s%s/%s' % (FAKE_SUBDOMAIN,
                                         breeze.ENDPOINTS.PEOPLE, person_id))
        self.assertEqual(res, json.loads(response.content))

    @defer.inlineCallbacks
    def test_get_events(self):
        response = MockResponse(200, json.dumps({'event_id': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)

        start_date = '3-1-2014'
        end_date = '3-7-2014'
        res = yield breeze_api.get_events(start_date=start_date, end_date=end_date)
        params = {
            "start": start_date,
            "end": end_date
        }
        url = FAKE_SUBDOMAIN + breeze.ENDPOINTS.EVENTS
        self.assertEqual(connection.url, url)
        self.assertEqual(connection.params, params)
        self.assertEqual(res, json.loads(response.content))

    @defer.inlineCallbacks
    def test_event_check_in(self):
        response = MockResponse(200, json.dumps({'event_id': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        res = yield breeze_api.event_check_in('person_id', 'event_id')
        url = "{}{}/attendance/add".format(FAKE_SUBDOMAIN, breeze.ENDPOINTS.EVENTS)
        params = {"instance_id": "event_id", "person_id": "person_id", "direction": "in"}
        self.assertEqual(connection.params, params)
        self.assertEqual(connection.url, url)
        self.assertEqual(res, json.loads(response.content))

    @defer.inlineCallbacks
    def test_event_check_out(self):
        response = MockResponse(200, json.dumps({'event_id': 'Some Data.'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        res = yield breeze_api.event_check_out('person_id', 'event_id')
        url = "{}{}/attendance/add".format(FAKE_SUBDOMAIN, breeze.ENDPOINTS.EVENTS)
        params = {"instance_id": "event_id", "person_id": "person_id", "direction": "out"}
        self.assertEqual(connection.params, params)
        self.assertEqual(connection.url, url)
        self.assertEqual(res, json.loads(response.content))

    @defer.inlineCallbacks
    def test_add_contribution(self):
        payment_id = '12345'
        response = MockResponse(
            200, json.dumps({'success': True,
                             'payment_id': payment_id}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        params = {
            "date": '3-1-2014',
            "name": 'John Doe',
            "person_id": '123456',
            "uid": 'UID',
            "processor": 'Processor',
            "method": 'Method',
            "funds_json": "[{'id': '12345', 'name': 'Fund', 'amount', '150.00' }]",
            "amount": '150.00',
            "group": 'Group',
            "batch_number": '100',
            "batch_name": 'Batch Name',
        }

        res = yield breeze_api.add_contribution(**params)
        url = "{}{}/add".format(FAKE_SUBDOMAIN, breeze.ENDPOINTS.CONTRIBUTIONS)
        self.assertEqual(connection.url, url)
        self.assertEqual(connection.params, params)
        self.assertEqual(res, payment_id)

    @defer.inlineCallbacks
    def test_edit_contribution(self):
        payment_id = '12345'
        new_payment_id = "99999"
        response = MockResponse(
            200, json.dumps({'success': True,
                             'payment_id': new_payment_id}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        params = {
            "payment_id": payment_id,
            "date": '3-1-2014',
            "name": 'John Doe',
            "person_id": '123456',
            "uid": 'UID',
            "processor": 'Processor',
            "method": 'Method',
            "funds_json": "[{'id': '12345', 'name': 'Fund', 'amount', '150.00' }]",
            "amount": '150.00',
            "group": 'Group',
            "batch_number": '100',
            "batch_name": 'Batch Name',
        }

        res = yield breeze_api.edit_contribution(**params)
        url = "{}{}/edit".format(FAKE_SUBDOMAIN, breeze.ENDPOINTS.CONTRIBUTIONS)
        self.assertEqual(connection.url, url)
        self.assertEqual(connection.params, params)
        self.assertEqual(res, new_payment_id)

    @defer.inlineCallbacks
    def test_list_contributions(self):
        response = MockResponse(
            200, json.dumps({'success': True,
                             'payment_id': '555'}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        start_date = '3-1-2014'
        end_date = '3-2-2014'
        person_id = '12345'
        include_family = True
        amount_min = '123456'
        amount_max = 'UID'
        method_ids = ['100', '101', '102']
        fund_ids = ['200', '201', '202']
        envelope_number = '1234'
        batches = ['300', '301', '302']
        forms = ['400', '401', '402']

        res = yield breeze_api.list_contributions(
            start_date=start_date,
            end_date=end_date,
            person_id=person_id,
            include_family=include_family,
            amount_min=amount_min,
            amount_max=amount_max,
            method_ids=method_ids,
            fund_ids=fund_ids,
            envelope_number=envelope_number,
            batches=batches,
            forms=forms
        )
        url = "{}{}/list".format(FAKE_SUBDOMAIN, breeze.ENDPOINTS.CONTRIBUTIONS)
        params = {
            "start": '3-1-2014',
            "end": '3-2-2014',
            "person_id": '12345',
            "include_family": 1,
            "amount_min": '123456',
            "amount_max": 'UID',
            "method_ids": '100-101-102',
            "fund_ids": '200-201-202',
            "envelope_number": '1234',
            "batches": '300-301-302',
            "forms": '400-401-402',
        }
        self.assertEquals(connection.url, url)
        self.assertEqual(res, json.loads(response.content))
        self.assertEqual(connection.params, params)

        # Ensure that an error gets thrown if person_id is not
        # provided with include_family.
        self.assertRaises(
            breeze.BreezeError,
            lambda: breeze_api.list_contributions(include_family=True))

    @defer.inlineCallbacks
    def test_delete_contribution(self):
        payment_id = '12345'
        response = MockResponse(
            200, json.dumps({'success': True,
                             'payment_id': payment_id}))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        res = yield breeze_api.delete_contribution(payment_id=payment_id)
        self.assertEquals(res, payment_id)
        url = "{}{}/delete".format(FAKE_SUBDOMAIN, breeze.ENDPOINTS.CONTRIBUTIONS)
        params = {"payment_id": payment_id}
        self.assertEqual(connection.url, url)
        self.assertEqual(connection.params, params)

    @defer.inlineCallbacks
    def test_list_funds(self):
        response = MockResponse(200, json.dumps([{
            "id": "12345",
            "name": "Adult Ministries",
            "tax_deductible": "1",
            "is_default": "0",
            "created_on": "2014-09-10 02:19:35"
        }]))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        res = yield breeze_api.list_funds(include_totals=True)
        self.assertEquals(res, json.loads(response.content))
        url = "{}{}/list".format(FAKE_SUBDOMAIN, breeze.ENDPOINTS.FUNDS)
        params = {"include_totals": 1}
        self.assertEquals(connection.url, url)
        self.assertEqual(connection.params, params)

    @defer.inlineCallbacks
    def test_list_campaigns(self):
        response = MockResponse(200, json.dumps([{
            "id": "12345",
            "name": "Building Campaign",
            "number_of_pledges": 65,
            "total_pledged": 13030,
            "created_on": "2014-09-10 02:19:35"
        }]))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection)
        res = yield breeze_api.list_campaigns()
        self.assertEquals(res, json.loads(response.content))
        url = "{}{}/list_campaigns".format(FAKE_SUBDOMAIN, breeze.ENDPOINTS.PLEDGES)
        self.assertEqual(connection.url, url)

    @defer.inlineCallbacks
    def test_list_pledges(self):
        response = MockResponse(200, json.dumps([{
            "id": "12345",
            "name": "Building Campaign",
            "number_of_pledges": 65,
            "total_pledged": 13030,
            "created_on": "2014-09-10 02:19:35"
        }]))
        connection = MockConnection(response)
        breeze_api = breeze.BreezeApi(
            breeze_url=FAKE_SUBDOMAIN,
            api_key=FAKE_API_KEY,
            connection=connection
        )
        res = yield breeze_api.list_pledges(campaign_id=329)
        self.assertEquals(res, json.loads(response.content))
        url = "{}{}/list_pledges".format(FAKE_SUBDOMAIN, breeze.ENDPOINTS.PLEDGES)
        params = {"campaign_id": 329}
        self.assertEqual(connection.params, params)
        self.assertEquals(connection.url, url)

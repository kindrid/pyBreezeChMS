"""Python wrapper for Breeze ChMS API: http://breezechms.com/docs#extensions_api

The Breeze API allows churches to build custom functionality integrated with
Breeze.

Usage:
  from breeze import breeze

  breeze_api = breeze.BreezeApi(
      breeze_url='https://demo.breezechms.com',
      api_key='5c2d2cbacg3...')
  people = breeze_api.GetPeople();

  for person in people:
    print '%s %s' % (person['first_name'], person['last_name'])
"""

__author__ = 'alex@rohichurch.org (Alex Ortiz-Rosado)'

import json
from datetime import datetime

import treq
from twisted.internet import defer

from txbreeze.utils import make_enum

ENDPOINTS = make_enum(
    'BreezeApiURL',
    PEOPLE='/api/people',
    EVENTS='/api/events',
    PROFILE_FIELDS='/api/profile',
    CONTRIBUTIONS='/api/giving',
    FUNDS='/api/funds',
    PLEDGES='/api/pledges')


class BreezeError(Exception):
    """Exception for BreezeApi."""
    pass


class BreezeApi(object):
    """A wrapper for the Breeze REST API."""

    def __init__(self, breeze_url, api_key, dry_run=False, connection=None):
        """Instantiates the BreezeApi with your Breeze account information.

        Args:
          breeze_url: Fully qualified domain for your organizations Breeze service.
          api_key: Unique Breeze API key. For instructions on finding your
                   organizations API key, see:
                   http://breezechms.com/docs#extensions_api
          dry_run: Enable no-op mode, which disables requests from being made. When
                   combined with debug, this allows debugging requests without
                   affecting data in your Breeze account."""

        self.breeze_url = breeze_url
        self.api_key = api_key
        self.dry_run = dry_run
        if connection:
            self.connection = connection
        else:
            self.connection = treq

        if not (self.breeze_url and self.breeze_url.startswith('https://') and
                self.breeze_url.endswith('.breezechms.com')):
            raise BreezeError('You must provide your breeze_url as ',
                              'subdomain.breezechms.com')

        if not self.api_key:
            raise BreezeError('You must provide an API key.')

    @defer.inlineCallbacks
    def _request(self, endpoint, params=None, headers=None, timeout=60):
        """Makes an HTTP request to a given url.

        Args:
          endpoint: URL where the service can be accessed.
          params: Query parameters to append to endpoint url.
          headers: HTTP headers; used for authenication parameters.
          timeout: Timeout in seconds for HTTP request.

        Returns:
          HTTP response

        Throws:
          BreezeError if connection or request fails."""

        headers = {'Content-Type': 'application/json', 'Api-Key': self.api_key}

        if params is None:
            params = {}
        keywords = dict(params=params, headers=headers, timeout=timeout)
        url = '{}{}'.format(self.breeze_url, endpoint)
        if self.dry_run:
            defer.returnValue(None)

        raw_response = yield self.connection.post(url, **keywords)
        try:
            response = yield treq.json_content(raw_response)
        except Exception as error:
            raise BreezeError(error.message)

        if not self._request_succeeded(response):
            raise BreezeError(response)
        defer.returnValue(response)

    def _request_succeeded(self, response):
        """Predicate to ensure that the HTTP request succeeded."""
        return not (('errors' in response) or ('errorCode' in response))

    def get_people(self, limit=None, offset=None, details=False):
        """List people from your database.

        Args:
          limit: Number of people to return. If None, will return all people.
          offset: Number of people to skip before beginning to return results.
                  Can be used in conjunction with limit for pagination.
          details: Option to return all information (slower) or just names.

        returns:
          JSON response. For example:
          {
            "id":"157857",
            "first_name":"Thomas",
            "last_name":"Anderson",
            "path":"img/profiles/generic/blue.jpg"
          },
          {
            "id":"157859",
            "first_name":"Kate",
            "last_name":"Austen",
            "path":"img/profiles/upload/2498d7f78s.jpg"
          },
          {
            ...
          }"""

        params = {}
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        if details:
            params["details"] = 1
        return self._request(ENDPOINTS.PEOPLE, params=params)

    def get_profile_fields(self):
        """List profile fields from your database.

        Returns:
          JSON response."""
        return self._request(ENDPOINTS.PROFILE_FIELDS)

    def get_person_details(self, person_id):
        """Retrieve the details for a specific person by their ID.

        Args:
          person_id: Unique id for a person in Breeze database.

        Returns:
          JSON response."""
        return self._request('{}/{}'.format(ENDPOINTS.PEOPLE, str(person_id)))

    def get_events(self, start_date=None, end_date=None):
        """Retrieve all events for a given date range.

        Args:
          start_date: Start date; defaults to first day of the current month.
          end_date: End date; defaults to last day of the current month

        Returns:
          JSON response."""
        params = {}
        if start_date:
            if isinstance(start_date, datetime):
                start_date = "{:%d-%m-%Y}".format(start_date)
            params["start"] = start_date
        if end_date:
            if isinstance(end_date, datetime):
                end_date = "{:%d-%m-%Y}".format(end_date)
            params["end"] = end_date
        return self._request(ENDPOINTS.EVENTS, params=params)

    def event_check_in(self, person_id, event_instance_id):
        """Checks in a person into an event.

        Args:
          person_id: id for a person in Breeze database.
          event_instance_id: id for event instance to check into.."""
        params = {
            "person_id": person_id,
            "instance_id": event_instance_id,
            "direction": "in"
        }
        endpoint = "{}/attendance/add".format(ENDPOINTS.EVENTS)
        return self._request(endpoint, params=params)

    def event_check_out(self, person_id, event_instance_id):
        """Remove the attendance for a person checked into an event.

        Args:
          person_id: Breeze ID for a person in Breeze database.
          event_instance_id: id for event instance to check out (delete).

        Returns:
          True if check-out succeeds; False if check-out fails."""

        params = {
            "person_id": person_id,
            "instance_id": event_instance_id,
            "direction": "out"
        }
        endpoint = "{}/attendance/add".format(ENDPOINTS.EVENTS)
        return self._request(endpoint, params=params)

    @defer.inlineCallbacks
    def add_contribution(self,
                         date=None,
                         name=None,
                         person_id=None,
                         uid=None,
                         processor=None,
                         method=None,
                         funds_json=None,
                         person_json=None,
                         amount=None,
                         group=None,
                         batch_number=None,
                         batch_name=None):
        """Add a contribution to Breeze.

        Args:
          date: Date of transaction in DD-MM-YYYY format (ie. 24-5-2015)
          name: Name of person that made the transaction. Used to help match up
                contribution to correct profile within Breeze.  (ie. John Doe)
          person_id: The Breeze ID of the donor. If unknown, use UID instead of
                     person id  (ie. 1234567)
          uid: The unique id of the person sent from the giving platform. This
               should be used when the Breeze ID is unknown. Within Breeze a user
               will be able to associate this ID with a given Breeze ID.
               (ie. 9876543)
          email: Email address of donor. If no person_id is provided, used to help
                 automatically match the person to the correct profile.
                 (ie. sample@breezechms.com)
          street_address: Donor's street address. If person_id is not provided,
                          street_address will be used to help automatically match
                          the person to the correct profile.  (ie. 123 Sample St)
          processor: The name of the processor used to send the payment. Used in
                     conjunction with uid. Not needed if using Breeze ID.
                     (ie. SimpleGive, BluePay, Stripe)
          method: The payment method. (ie. Check, Cash, Credit/Debit Online,
                  Credit/Debit Offline, Donated Goods (FMV), Stocks (FMV),
                  Direct Deposit)
          funds_json: JSON string containing fund names and amounts. This allows
                      splitting fund giving. The ID is optional. If present, it must
                      match an existing fund ID and it will override the fund name.
                      ie. [ {
                              'id':'12345',
                              'name':'General Fund',
                              'amount':'100.00'
                            },
                            {
                              'name':'Missions Fund',
                              'amount':'150.00'
                            }
                          ]
          amount: Total amount given. Must match sum of amount in funds_json.
          group: This will create a new batch and enter all contributions with the
                 same group into the new batch. Previous groups will be remembered
                 and so they should be unique for every new batch. Use this if
                 wanting to import into the next batch number in a series.
          batch_number: The batch number to import contributions into. Use group
                        instead if you want to import into the next batch number.
          batch_name: The name of the batch. Can be used with batch number or group.

        Returns:
          Payment Id.

        Throws:
          BreezeError on failure to add contribution."""

        params = {}
        if date:
            if isinstance(date, datetime):
                date = "{:%d-%m-%Y}".format(date)
            params["date"] = date
        if name:
            params["name"] = name
        if person_id:
            params["person_id"] = person_id
        if uid:
            params["uid"] = uid
        if processor:
            params["processor"] = processor
        if method:
            params["method"] = method
        if funds_json:
            if not isinstance(funds_json, basestring):
                funds_json = json.dumps(funds_json)
            params["funds_json"] = funds_json
        if person_json:
            if not isinstance(person_json, basestring):
                person_json = json.dumps(person_json)
            params["person_json"] = person_json
        if amount:
            params["amount"] = amount
        if group:
            params["group"] = group
        if batch_number:
            params["batch_number"] = batch_number
        if batch_name:
            params["batch_name"] = batch_name
        endpoint = "{}/add".format(ENDPOINTS.CONTRIBUTIONS)
        response = yield self._request(endpoint, params=params)
        defer.returnValue(response['payment_id'])

    @defer.inlineCallbacks
    def edit_contribution(self,
                          payment_id=None,
                          date=None,
                          name=None,
                          person_id=None,
                          uid=None,
                          processor=None,
                          method=None,
                          funds_json=None,
                          amount=None,
                          group=None,
                          batch_number=None,
                          batch_name=None):
        """Edit an existing contribution.

        Args:
          payment_id: The ID of the payment that should be modified.
          date: Date of transaction in DD-MM-YYYY format (ie. 24-5-2015)
          name: Name of person that made the transaction. Used to help match up
                contribution to correct profile within Breeze.  (ie. John Doe)
          person_id: The Breeze ID of the donor. If unknown, use UID instead of
                     person id  (ie. 1234567)
          uid: The unique id of the person sent from the giving platform. This
               should be used when the Breeze ID is unknown. Within Breeze a user
               will be able to associate this ID with a given Breeze ID.
               (ie. 9876543)
          email: Email address of donor. If no person_id is provided, used to help
                 automatically match the person to the correct profile.
                 (ie. sample@breezechms.com)
          street_address: Donor's street address. If person_id is not provided,
                          street_address will be used to help automatically match
                          the person to the correct profile.  (ie. 123 Sample St)
          processor: The name of the processor used to send the payment. Used in
                     conjunction with uid. Not needed if using Breeze ID.
                     (ie. SimpleGive, BluePay, Stripe)
          method: The payment method. (ie. Check, Cash, Credit/Debit Online,
                  Credit/Debit Offline, Donated Goods (FMV), Stocks (FMV),
                  Direct Deposit)
          funds_json: JSON string containing fund names and amounts. This allows
                      splitting fund giving. The ID is optional. If present, it must
                      match an existing fund ID and it will override the fund name.
                      ie. [ {
                              'id':'12345',
                              'name':'General Fund',
                              'amount':'100.00'
                            },
                            {
                              'name':'Missions Fund',
                              'amount':'150.00'
                            }
                          ]
          amount: Total amount given. Must match sum of amount in funds_json.
          group: This will create a new batch and enter all contributions with the
                 same group into the new batch. Previous groups will be remembered
                 and so they should be unique for every new batch. Use this if
                 wanting to import into the next batch number in a series.
          batch_number: The batch number to import contributions into. Use group
                        instead if you want to import into the next batch number.
          batch_name: The name of the batch. Can be used with batch number or group.

        Returns:
          Payment id.

        Throws:
          BreezeError on failure to edit contribution."""

        params = {}
        if payment_id:
            params["payment_id"] = payment_id
        if date:
            if isinstance(date, datetime):
                date = "{:%d-%m-%Y}".format(date)
            params["date"] = date
        if name:
            params["name"] = name
        if person_id:
            params["person_id"] = person_id
        if uid:
            params["uid"] = uid
        if processor:
            params["processor"] = processor
        if method:
            params["method"] = method
        if funds_json:
            params["funds_json"] = funds_json
        if amount:
            params["amount"] = amount
        if group:
            params["group"] = group
        if batch_number:
            params["batch_number"] = batch_number
        if batch_name:
            params["batch_name"] = batch_name
        endpoint = "{}/edit".format(ENDPOINTS.CONTRIBUTIONS)
        response = yield self._request(endpoint, params=params)
        defer.returnValue(response['payment_id'])

    @defer.inlineCallbacks
    def delete_contribution(self, payment_id):
        """Delete an existing contribution.

        Args:
          payment_id: The ID of the payment that should be deleted.

        Returns:
          Payment id.

        Throws:
          BreezeError on failure to delete contribution."""
        endpoint = "{}/delete".format(ENDPOINTS.CONTRIBUTIONS)
        params = {"payment_id": payment_id}
        response = yield self._request(endpoint, params=params)
        defer.returnValue(response['payment_id'])

    def list_contributions(self,
                           start_date=None,
                           end_date=None,
                           person_id=None,
                           include_family=False,
                           amount_min=None,
                           amount_max=None,
                           method_ids=None,
                           fund_ids=None,
                           envelope_number=None,
                           batches=None,
                           forms=None):
        """Retrieve a list of contributions.

        Args:
          start_date: Find contributions given on or after a specific date
                      (ie. 2015-1-1); required.
          end_date: Find contributions given on or before a specific date
                    (ie. 2018-1-31); required.
          person_id: ID of person's contributions to fetch. (ie. 9023482)
          include_family: Include family members of person_id (must provide
                          person_id); default: False.
          amount_min: Contribution amounts equal or greater than.
          amount_max: Contribution amounts equal or less than.
          method_ids: List of method IDs.
          fund_ids: List of fund IDs.
          envelope_number: Envelope number.
          batches: List of Batch numbers.
          forms: List of form IDs.

        Returns:
          List of matching contributions.

        Throws:
          BreezeError on malformed request."""

        params = {}
        if start_date:
            if isinstance(start_date, datetime):
                start_date = "{:%d-%m-%Y}".format(start_date)
            params["start"] = start_date
        if end_date:
            if isinstance(end_date, datetime):
                end_date = "{:%d-%m-%Y}".format(end_date)
            params["end"] = end_date
        if person_id:
            params["person_id"] = person_id
        if include_family:
            if not person_id:
                raise BreezeError('include_family requires a person_id.')
            params["include_family"] = 1
        if amount_min:
            params["amount_min"] = amount_min
        if amount_max:
            params["amount_max"] = amount_max
        if method_ids:
            params["method_ids"] = "-".join(method_ids)
        if fund_ids:
            params["fund_ids"] = "-".join(fund_ids)
        if envelope_number:
            params["envelope_number"] = envelope_number
        if batches:
            params["batches"] = "-".join(batches)
        if forms:
            params["forms"] = "-".join(forms)
        endpoint = "{}/list".format(ENDPOINTS.CONTRIBUTIONS)
        return self._request(endpoint, params=params)

    def list_funds(self, include_totals=False):
        """List all funds.

        Args:
          include_totals: Amount given to the fund should be returned.

        Returns:
          JSON Reponse."""

        params = {}
        if include_totals:
            params["include_totals"] = 1
        endpoint = "{}/list".format(ENDPOINTS.FUNDS)
        return self._request(endpoint, params=params)

    def list_campaigns(self):
        """List of campaigns.

        Returns:
          JSON response."""
        return self._request('{}/list_campaigns'.format(ENDPOINTS.PLEDGES))

    def list_pledges(self, campaign_id):
        """List of pledges within a campaign.

        Args:
          campaign_id: ID number of a campaign.

        Returns:
          JSON response."""
        endpoint = "{}/list_pledges".format(ENDPOINTS.PLEDGES)
        params = {"campaign_id": campaign_id}
        return self._request(endpoint, params=params)

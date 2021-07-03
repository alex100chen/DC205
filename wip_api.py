"""
Methods for interacting with the WIP-Tracking database API for storing
test results
"""
import shelve
import time
import queue
import threading
from functools import wraps, lru_cache
from json.decoder import JSONDecodeError

import requests
#from pubsub import pub

#from git_version import get_version
#from device_tests import TestResult, timestamp_now


class ApiError(Exception):
    """Generic error from the API Client"""

    def __init__(self, message, code=None, url=None):
        self.message, self.code, self.url = message, code, url


class AuthenticationError(ApiError):
    """The username and/or password is invalid"""


class PermissionDeniedError(ApiError):
    """We were not allowed to do something for lack of permissions"""


class UrlInvalid(ApiError):
    """A given URL is invalid"""


class ApiConnectionError(ApiError):
    """We could not reach the API server"""


class NoResourceError(ApiError):
    """Nothing was returned by that particular query"""


class DutNotRegisteredError(NoResourceError):
    """The DUT wasn't registered with the API"""


class ApiClient:
    def __init__(self, root_url, username, password, test_station_url, test_type_url):
        """Initialize our state and check the given credentials, URLs
        Throw exceptions if anything is out of place
        """
        self.root_url = root_url
        self.test_station_url = test_station_url
        self.test_type_url = test_type_url
        self.http_session = requests.Session()
        self.http_session.auth = (username, password)

        # this has to be initialized before we can call self.get()
        self._url_map = {}
        self.test_station = None
        self.test_type = None

    def connect(self):
        """Attempt to connect to the API, read the URL map"""
        # will throw an error if the root_url is invalid
        self._url_map = self.get(self.root_url)
        for route in ['parts', 'built-parts', 'test-stations', 'test-types',
                      'manufacturing-test-results', 'manufacturing-test-sessions',
                      'build-stages']:
            if route not in self._url_map:
                raise ApiError(
                    f"API root was missing expected route: {route}. "
                    "Someone may have broken the API."
                )

        # will throw an error if the test_type_url or the authentication
        # credentials are invalid
        self.update_test_station()
        self.update_test_type()

    def disconnect(self):
        pass

    def update_test_station(self):
        self.test_station = self.get(self.test_station_url)
        if self.test_type_url not in self.test_station['test_types']:
            raise ApiError(
                f"The API reports that test type {self.test_type_url} is not "
                f"a valid option for test station {self.test_station_url} - "
                "are those URLs correct? Is that test type registered under that test station?"
            )

    def update_test_type(self):
        self.test_type = self.get(self.test_type_url)

    def get(self, url_or_path, params=None, **kwargs):
        return self.call_api('get', url_or_path, params=params, **kwargs)

    def post(self, url_or_path, json=None, **kwargs):
        return self.call_api('post', url_or_path, json=json, **kwargs)

    def patch(self, url_or_path, json=None, **kwargs):
        return self.call_api('patch', url_or_path, json=json, **kwargs)

    def get_paginated(self, url_or_path, params=None, **kwargs):
        """Unroll paginated calls by getting every reference to 'next' sequentially
        Return the sum total of all 'results' in those responses
        TODO: put a limit on this if it gets out of hand
        """
        response = self.get(url_or_path, params=params, **kwargs)
        results = response['results']
        while response['next'] is not None:
            try:
                response = self.get(response['next'], params=params, **kwargs)
                results += response['results']
            except:
                try:
                    response = self.get(response['next'], params=params, **kwargs)
                    results += response['results']
                except:
                    print("Error: could not get API data")

        return results

    def call_api(self, method_name, url_or_path, **kwargs):
        """Call the API at the given URL (or path)
        Use the given method_name as an http verb
        url_or_path can be a fully qualified URL, or the name of an
        endpoint found in the URL map. The latter is preferred because
        it's less susceptible to breaking if the URL map changes.
        Throw proper exceptions if anything goes wrong
        """
        assert method_name in ['get', 'post', 'patch']
        url = self._url_map.get(url_or_path, url_or_path)
        method = getattr(self.http_session, method_name)
        try:
            r = method(url=url, **kwargs, timeout=60)
            #print(r.json())
        except requests.exceptions.ConnectionError:
            raise ApiConnectionError(
                f"Could not make contact with the API server at: {url}",
                url=url,
            )
        except requests.exceptions.RequestException as err:
            raise ApiError(
                str(err), url=url_or_path,
            )
        if r.status_code in [403]:
            raise PermissionDeniedError(
                "Unable to authenticate with API using given username/password "
                "or forbidden to perform the last action",
                code=r.status_code, url=url,
            )
        if r.status_code in [404]:
            raise UrlInvalid(
                f"The API server couldn't find the URL: {url}",
                code=r.status_code, url=url,
            )
        if r.status_code not in [200, 201, 202]:
            try:
                json_data = r.json()
            except JSONDecodeError:
                json_data = None
            raise ApiConnectionError(
                (f"API returned a bad HTTP status code: {r.status_code}\n"
                 f"Reason: {r.reason} - {json_data}"),
                code=r.status_code, url=url,
            )
        try:
            return r.json()
        except JSONDecodeError:
            raise ApiConnectionError(
                f"Was not able to decode response from API: {str(r)}"
            )

    @lru_cache(maxsize=16)
    def get_part(self, part_number, revision):
        """Query the API for the given (part_number, revision) combo
        and return what was there
        If we've already done that recently, get the info from a cache
        """
        part_types = self.get_paginated('parts', params={'number': part_number,
                                                         'revision': revision})
        if len(part_types) == 0:
            raise NoResourceError(
                f"There appears to be no {part_number} Rev. {revision} in "
                "the API, has it been registered yet?"
            )
        return part_types[0]

    @lru_cache(maxsize=16)
    def get_built_part(self, serial_number):
        """Query the API for the given serial number and return
        what was there
        """
        built_parts = self.get_paginated('built-parts',
                                         params={'serial_number': serial_number})
        if len(built_parts) == 0:
            raise DutNotRegisteredError(
                f"Serial number {serial_number} was not found in the API. "
                "Did you mean to register it first?"
            )
        return built_parts[0]

    def get_test_session(self, session_id):
        """Get a single session by id"""
        sessions = self.get_paginated('manufacturing-test-sessions',
                                      params={'id': session_id})
        if len(sessions) != 1:
            raise NoResourceError(
                f"API returned {len(sessions)} sessions for ID: {session_id}"
            )
        return sessions[0]

    @lru_cache(maxsize=2)
    def get_build_stage(self):
        """Make a best-effort at finding a build stage to register new parts with
        """
        build_stages = self.get_paginated('build-stages',
                                          params={'name__icontains': 'test'})
        if len(build_stages) == 0:
            raise NoResourceError(
                "Cannot guess a proper build stage to create parts with. "
                "Please register all parts in the API before testing them."
            )
        return build_stages[0]

    def create_built_part(self, serial_number, part_number, revision):
        """Create a built_part object in the database with the given
        details and return the response from the API details
        """
        part_type = self.get_part(part_number, revision)
        if part_type['url'] not in self.test_type['parts']:
            # double check before annoying the user (we cache the test type details)
            self.update_test_type()

            if part_type['url'] not in self.test_type['parts']:
                raise ApiError(
                    f"{part_number} Rev. {revision} does not appear to be a valid "
                    f"part for the {self.test_type['description']} - did you mean "
                    "to link them together in the API first?"
                )

        # built parts need a serial number, location, build stage, and a part type
        payload = {
            'serial_number': serial_number,
            'build_stage': self.get_build_stage()['url'],
            'part': part_type['url'],
        }
        return self.post('built-parts', json=payload)

    def search_test_sessions(self, serial_number, finished=None):
        """Get all test sessions associated with the given serial number
        Limit results to tests performed by testers of our type
        If finished is True, limit the results to only open sessions
        If finished is False, limit the results to only closed sessions
        """
        assert finished in [True, False, None]
        params = {
            'serial_number': serial_number,
            'test_type_id': self.test_type['id'],
        }
        if finished is not None:
            params['is_finished'] = finished
        return self.get_paginated('manufacturing-test-sessions', params=params)

    def search_test_sessions_allsnums(self, finished=None):
        """Get all test sessions associated with the given test type
        Limit results to tests performed by testers of our type
        If finished is True, limit the results to only open sessions
        If finished is False, limit the results to only closed sessions
        """
        assert finished in [True, False, None]
        params = {
            'test_type_id': self.test_type['id'],
        }
        if finished is not None:
            params['is_finished'] = finished
        return self.get_paginated('manufacturing-test-sessions', params=params)

    def search_built_parts(self, part_number, finished=None):
        """Get all test sessions associated with the given serial number
        Limit results to tests performed by testers of our type
        If finished is True, limit the results to only open sessions
        If finished is False, limit the results to only closed sessions
        """
        assert finished in [True, False, None]
        params = {
            'part_number': part_number,
        }
        if finished is not None:
            params['is_finished'] = finished
        return self.get_paginated('built-parts', params=params)

    def search_test_metadata(self, part_number, finished=None):
        """Get all test sessions associated with the given serial number
        Limit results to tests performed by testers of our type
        If finished is True, limit the results to only open sessions
        If finished is False, limit the results to only closed sessions
        """
        assert finished in [True, False, None]
        params = {
            'part_number': part_number,
        }
        if finished is not None:
            params['is_finished'] = finished
        return self.get_paginated('test-result-metadata', params=params)

    def get_test_session_results(self, test_session_id):
        """Get test results from the given session_id
        Returns a list of TestResult objects re-constructed from API data
        """
        query_results = self.get_paginated(
            'manufacturing-test-results',
            params={'parent_result_id': test_session_id}
        )
        results = []
        for result_dict in query_results:
            # construct a nearly-bare result object
            test_class_name = result_dict.pop('test_short_name')
            test_id = result_dict['result_details'].pop('test_id', None)
            result = TestResult(test_class_name, test_id)

            # re-set all the attributes as they ware during serialization
            for attr in ['start_time', 'stop_time', 'passed', 'log', 'id']:
                setattr(result, attr, result_dict.pop(attr))
            result.__dict__.update(result_dict.pop('result_details'))

            # what API data is left from the query goes in this attribute
            result.api_metadata = result_dict
            results.append(result)
        return results

    def create_new_test_session(self, built_part_url):
        """Create a new test session in the database for a given built part
        Return the session object that was created
        """
        payload = {
            'built_part': built_part_url,
            'test_station': self.test_station_url,
            'test_type': self.test_type_url,
            'start_time': timestamp_now(),
            'test_code_version': get_version(),
        }
        return self.post("manufacturing-test-sessions", json=payload)

    def create_new_test_result(self, test_session, result):
        """Create a new test result in the database associated with
        the given test session ob
        ject
        'test_session' is a dictionary as returned by create_new_session() or get_test_sessions()
        'result' is a dictionary as might be generated by device_tests.TestResult.__dict__
        """
        # don't change the result object we were passed when we pop items off
        result = result.copy()
        payload = {
            'parent_result': test_session['url'],
            'test_station': self.test_station_url,
            'test_type': self.test_type_url,
            'built_part': test_session['built_part'],
            #'start_time': test_session['start_time'],

            # pop items so they don't also show up in result_details
            'start_time': result.pop('start_time', None),
            'stop_time': result.pop('stop_time', None),
            'passed': result.pop('passed', False),
            'test_short_name': result.pop('test_short_name', None),
            'test_code_version': get_version(),
            'log': result.pop('log', ""),

            # everything else in the result object shows up here
            'result_details': result,
        }
        return self.post("manufacturing-test-results", json=payload)

    def mark_session_complete(self, test_session, passed):
        """Mark the currently open test session as complete with
        the given result
        """
        payload = {
            'stop_time': timestamp_now(),
            'passed': passed,
        }
        return self.patch(test_session['url'], json=payload)


class LocalShelveClient:
    def __init__(self, db_name):
        """Create client. Remember database name"""
        self.db_name = db_name
        self.db = None
        self.test_station = {
            "id": 1,
            "url": "/api/test-stations/1/",
            "test_types": ["/api/test-types/1/"],
            "name": "Test Station"
        }
        self.test_type = {
            "id": 1,
            "url": "/api/test-types/1/",
            "parts": ["/api/parts/1/"],
            "description": "Test and Calibration"
        }

    def connect(self):
        """Attempt to connect to the database"""
        if not self.db:
            self.db = shelve.open(self.db_name)

    def disconnect(self):
        """Close connection"""
        if self.db:
            self.db.close()
        self.db = None

    def get_part(self, part_number, revision):
        """Query for the given (part_number, revision) combo
        This is stubbed out. It returns a reasonable fake entry
        """
        return {
            "url": "/api/parts/1/",
            "human_url": "/wip-tracker/final-good-nums/1/",
            "number": f"{part_number}",
            "description": "SRS Generic Product",
            "revision": f"{revision}",
            "created": time.mktime((2019,1,1,0,0,0,0,1,-1)),
            "lifecycle": "DESIGN",
            "is_final_good": True
        }

    def get_built_part(self, serial_number):
        """Query for the given serial number
        This is stubbed out. It returns a reasonable fake entry
        """
        return self.create_built_part(serial_number, '/api/parts/1/', "A")

    def get_test_session(self, session_id):
        """Get a single session by id"""
        db_session_id = f"session_{session_id}"
        session = {}
        if db_session_id in self.db:
            session = self.db[db_session_id]
        return session

    def get_build_stage(self):
        return {
            "url": "/api/build-stages/1/",
            "human_url": "/wip-tracker/stages/1/",
            "id": 1,
            "name": "Test and Calibration"
        }

    def create_built_part(self, serial_number, part_number, revision):
        """Create a built_part object in the database with the given
        details and return the response from the API details
        """
        if type(serial_number) == bytes:
            serial_number = serial_number.decode()
        part = {
            "url": f"/api/built-parts/{serial_number}/",
            "human_url": f"/wip-tracker/final-goods/{serial_number}/",
            "serial_number": f"{serial_number}",
            "build_stage": "/api/build-stages/1/",
            "part": "/api/parts/1/",
            "parent": None,
            "order_number": None
        }
        return part

    def search_test_sessions(self, serial_number, finished=None):
        """Get all test sessions associated with the given serial number
        If finished is True, limit the results to only open sessions
        If finished is False, limit the results to only closed sessions
        """
        str_serial = f'{serial_number}'
        session_ids = []
        if str_serial in self.db:
            session_ids = self.db[str_serial]
        sessions = []
        for session_id in session_ids:
            db_session_id = f"session_{session_id}"
            if db_session_id in self.db:
                sessions.append(self.db[db_session_id])
        if finished is not None:
            sessions = [session for session in sessions if (session['stop_time'] is not None) == finished]
        return sessions

    def get_test_session_results(self, session_id):
        """Get test results from the given session_id
        Returns a list of TestResult objects re-constructed from API data
        """
        db_session_id = f"session_{session_id}"
        results = []
        if db_session_id in self.db:
            db_results= self.db[db_session_id]['child_results']
            for result_dict in db_results:
                # construct a nearly-bare result object
                test_class_name = result_dict.pop('test_short_name')
                test_id = result_dict['result_details'].pop('test_id', None)
                result = TestResult(test_class_name, test_id)

                # re-set all the attributes as they ware during serialization
                for attr in ['start_time', 'stop_time', 'passed', 'log']:
                    setattr(result, attr, result_dict.pop(attr))
                result.__dict__.update(result_dict.pop('result_details'))

                # what API data is left from the query goes in this attribute
                result.api_metadata = result_dict
                results.append(result)
        return results

    def create_new_test_session(self, built_part_url):
        """Create a new test session in the database for a given built part
        Return the session object that was created
        """
        start_slash = built_part_url[0:-1].rfind('/')
        serial_number = built_part_url[start_slash+1:-1]
        max_session = 1
        if 'max_session' in self.db:
            max_session = self.db['max_session'] + 1
        self.db['max_session'] = max_session
        session_ids = []
        if serial_number in self.db:
            session_ids = self.db[serial_number]
        session_ids.append(max_session)
        self.db[serial_number] = session_ids
        db_session_id = f"session_{max_session}"
        session = {
            "id": max_session,
            "url": f"/api/manufacturing-test-results/f{max_session}/",
            "human_url": "/wip-tracker/results/f{max_session}/",
            "test_type": "/api/test-types/1/",
            "test_station": "/api/test-stations/1/",
            "built_part": built_part_url,
            "parent_result": None,
            "created_by": "tcal",
            "start_time": timestamp_now(),
            "stop_time": None,
            "test_short_name": None,
            "test_code_version": "unknown repository",
            "passed": None,
            "log": None,
            "result_details": None,
            "child_results": []
        }
        self.db[db_session_id] = session
        return session

    def create_new_test_result(self, test_session, result):
        """Create a new test result in the database associated with
        the given test session object
        'test_session' is a dictionary as returned by create_new_session() or get_test_sessions()
        'result' is a dictionary as might be generated by device_tests.TestResult.__dict__
        """
        # don't change the result object we were passed when we pop items off
        result = result.copy()
        db_result = {
            'parent_result': test_session['url'],
            'test_station': self.test_station['url'],
            'test_type': self.test_type['url'],
            'built_part': test_session['built_part'],

            # pop items so they don't also show up in result_details
            'start_time': result.pop('start_time', None),
            'stop_time': result.pop('stop_time', None),
            'passed': result.pop('passed', False),
            'test_short_name': result.pop('test_class_name', None),
            'test_code_version': get_version(),
            'log': result.pop('log', ""),

            # everything else in the result object shows up here
            'result_details': result,
        }
        db_session_id = f"session_{test_session['id']}"
        if db_session_id in self.db:
            session = self.db[db_session_id]
            session["child_results"].append(db_result)
            self.db[db_session_id] = session
        return db_result

    def mark_session_complete(self, test_session, passed):
        """Mark the currently open test session as complete with
        the given result
        """
        db_session_id = f"session_{test_session['id']}"
        session = {}
        if db_session_id in self.db:
            session = self.db[db_session_id]
            session['stop_time'] = timestamp_now()
            session['passed'] = passed
            self.db[db_session_id] = session
        return session


def queued_task(task_func):
    """Transform a function into one that issues itself into a queue
    instead of just running directly
    Decorate functions with this to allow them to be called from
    another thread safely
    Decorated functions' return values will be ignored, so return
    things from them using pub.sendMessage()
    """
    @wraps(task_func)
    def task_queuer(self, *args, **kwargs):
        task = (task_func, args, kwargs)
        self.task_queue.put(task)

    return task_queuer


class DummyApiConnection:
    """Use this instead of an ApiConnectionThread to stub out the API"""
    def __init__(self, app_settings):
        self.app_settings = app_settings

    def stop(self):
        pass

    def start_test_session(self, serial_number):
        pass

    def end_test_session(self):
        pass

    def upload_test_result(self, result):
        pass

    def query_existing_sessions(self, serial_number):
        pass

    def reopen_test_session(self, session_id):
        pass


class ApiConnectionThread(threading.Thread):
    """Handle API requests in the background via a queue
    Sends messages out using pyPubSub that can be subscribed to
    """

    def __init__(self, app_settings):
        super(ApiConnectionThread, self).__init__(daemon=True)
        self.app_settings = app_settings
        self.task_queue = queue.Queue()
        api_config = (
            app_settings.api_root_url,
            app_settings.api_test_station_url,
            app_settings.api_test_type_url,
            app_settings.api_username,
            app_settings.api_password,
        )
        self.client = create_database_client(app_settings.database_client, api_config)
        self.test_session = None
        self.stop_event = threading.Event()

    def run(self):
        """Connect to the API and service tasks on the queue"""
        try:
            self.client.connect()
            pub.sendMessage('api.connect', connected=True)
        except ApiError as err:
            pub.sendMessage('api.connect', connected=False)
            pub.sendMessage('api.error', error=err)
            return

        while not self.stop_event.is_set():
            try:
                task_func, args, kwargs = self.task_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                task_func(self, *args, **kwargs)
                pub.sendMessage('api.completed', task_name=task_func.__name__)
            except Exception as err:
                pub.sendMessage('api.error', error=err)
        self.client.disconnect()

    def stop(self, timeout=None):
        pub.sendMessage('api.connect', connected=False)
        self.stop_event.set()
        self.join(timeout=timeout)

    @queued_task
    def start_test_session(self, serial_number, part_number=None, revision=None):
        """Start a new test session
        First check if the serial number has been registered, if it hasn't,
        try to register one using the given part number and revision
        Once the session has been opened, issue a message on api.session_opened
        with no results (none exist yet) to inform the main window
        """
        try:
            built_part = self.client.get_built_part(serial_number=serial_number)
        except NoResourceError:
            if part_number is None or revision is None:
                raise DutNotRegisteredError(
                    f"Serial number {serial_number} has not been registered yet "
                    "and part_number and revision were not supplied to register it"
                )
            # try to register the serial number
            built_part = self.client.create_built_part(serial_number, part_number, revision)

        if built_part['part'] not in self.client.test_type['parts']:
            raise ApiError(
                f"It looks like '{self.client.test_type['description']}' does "
                "not support testing parts of this type\n\n"
                f"Part type:  {built_part['part']}\n\n"
                "Did you mean to register that part type with that test type beforehand?\n\n"
                "Is the Test Type API URL configured properly?"
            )

        self.test_session = self.client.create_new_test_session(built_part['url'])
        pub.sendMessage(
            'api.session_opened', results=[],
            human_url=self.test_session['human_url'],
            session_id=self.test_session['id'],
        )

    @queued_task
    def end_test_session(self):
        """Close the currently open test session"""
        self.test_session = None

    @queued_task
    def mark_session_complete(self, passed):
        """Mark the currently open session as complete"""
        if self.test_session is None:
            raise ApiError("Cannot mark a session complete if none is open")

        self.client.mark_session_complete(self.test_session, passed)

    @queued_task
    def upload_test_result(self, result):
        """Upload the given result object to the API
        Must start a test session before calling this
        """
        if self.test_session is None:
            raise ApiError("Cannot upload result before a test session has started")

        self.client.create_new_test_result(self.test_session, result.__dict__)

    @queued_task
    def query_existing_sessions(self, serial_number, finished=None):
        """Query the API for existing sessions using the given serial number
        If finished is True, limit the results to only open sessions
        If finished is False, limit the results to only closed sessions
        """
        sessions = self.client.search_test_sessions(serial_number, finished=finished)
        pub.sendMessage('api.session_query', sessions=sessions)

    @queued_task
    def reopen_test_session(self, session_id):
        """Reopen the given session
        Issue a message on api.session_opened with a list of the
        previous results from the reopened session
        """
        self.test_session = self.client.get_test_session(session_id)
        results = self.client.get_test_session_results(session_id)
        pub.sendMessage(
            'api.session_opened', results=results,
            human_url=self.test_session['human_url'],
            session_id=self.test_session['id'],
        )


def create_database_client(client_type, api_config):
    if "local" == client_type:
        client = LocalShelveClient("data/tcal")
    else:
        (root_url, test_station_url, test_type_url, username, password) = api_config
        client = ApiClient(
            root_url=root_url,
            username=username,
            password=password,
            test_station_url=test_station_url,
            test_type_url=test_type_url,
        )
    return client
import time

import pymongo

from flask_pymongo.tests.util import FlaskRequestTest
import flask_pymongo


class FlaskPyMongoConfigTest(FlaskRequestTest):

    def setUp(self):
        super(FlaskPyMongoConfigTest, self).setUp()

        conn = pymongo.MongoClient(port=self.port)
        conn.test_db.command(
            "createUser",
            "flask",
            pwd="pymongo",
            roles=["readWrite"],
        )

    def tearDown(self):
        super(FlaskPyMongoConfigTest, self).tearDown()

        conn = pymongo.MongoClient(port=self.port)
        conn.test_db.command("dropUser", "flask")

        conn.drop_database(self.dbname)
        conn.drop_database(self.dbname + "2")

    def test_config_with_uri_in_flask_conf_var(self):
        uri = "mongodb://localhost:{}/{}".format(self.port, self.dbname)
        self.app.config["MONGO_URI"] = uri

        mongo = flask_pymongo.PyMongo(self.app)

        _wait_until_connected(mongo)
        assert mongo.db.name == self.dbname
        assert ("localhost", self.port) == mongo.cx.address

    def test_config_with_uri_passed_directly(self):
        uri = "mongodb://localhost:{}/{}".format(self.port, self.dbname)

        mongo = flask_pymongo.PyMongo(self.app, uri)

        _wait_until_connected(mongo)
        assert mongo.db.name == self.dbname
        assert ("localhost", self.port) == mongo.cx.address

    def test_multiple_pymongos(self):
        uri1 = "mongodb://localhost:{}/{}".format(self.port, self.dbname)
        uri2 = "mongodb://localhost:{}/{}".format(self.port, self.dbname + "2")

        mongo1 = flask_pymongo.PyMongo(self.app, uri1)  # noqa: F841 unused variable
        mongo2 = flask_pymongo.PyMongo(self.app, uri2)  # noqa: F841 unused variable

        # this test passes if it raises no exceptions

    def test_custom_document_class(self):
        class CustomDict(dict):
            pass

        uri = "mongodb://localhost:{}/{}".format(self.port, self.dbname)
        mongo = flask_pymongo.PyMongo(self.app, uri, document_class=CustomDict)
        assert mongo.db.things.find_one() is None, "precondition failed"

        mongo.db.things.insert_one({"_id": "thing", "val": "foo"})

        assert type(mongo.db.things.find_one()) == CustomDict


def _wait_until_connected(mongo, timeout=1.0):
    start = time.time()
    while time.time() < (start + timeout):
        if mongo.cx.nodes:
            return
        time.sleep(0.05)
    raise RuntimeError("could not prove mongodb connected in %r seconds" % timeout)
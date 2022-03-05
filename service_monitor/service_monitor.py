#!/usr/bin/env python3

import os
import urllib.request
import urllib.error
import unittest

import boto3

SETTINGS = None
def get_settings():
    global SETTINGS
    if SETTINGS is None:
        SETTINGS = dict()
        SETTINGS["region"] = os.environ.get("region")
        SETTINGS["profile"] = os.environ.get("profile")
        SETTINGS["from_addr"] = os.environ["email_from"]
        SETTINGS["to_addr"] = os.environ["email_to"]
        SETTINGS["url"] = os.environ["monitor_url"]
        SETTINGS["expect"] = int(os.environ["expect_code"])
    return SETTINGS
    

def alert_failed(msg_txt: str = "Connection fail") -> None:
    settings = get_settings()
    subject = "ALERT: Service Monitor"
    body = f"URL: {settings['url']}\nMSG: {msg_txt}"

    sess = boto3.session.Session(region_name=settings["region"],
            profile_name=settings["profile"])
    ses = sess.client("ses")
    response = ses.send_email(
        Source = settings["from_addr"],
        Destination = {"ToAddresses": [settings["to_addr"]]},
        Message = {
            "Subject": {"Data": subject},
            "Body": {"Text": {"Data": body} },
        }
    )

    print(f"SES Response: {response}")

def run_monitor():
    settings = get_settings()
    req = urllib.request.Request(settings["url"])
    try:
        with urllib.request.urlopen(req, timeout=1) as urlf:
            data = urlf.read()
    except urllib.error.HTTPError as err:
        if err.status == settings["expect"]:
            print(f"Success - {settings['expect']} as expected")
            return True
        else:
            raise err
    else:
        print("Data received: {}".format(len(data)))
        if settings["expect"] == 200:
            return True
        else:
            raise RuntimeError("Status was 200, unexpectedly")
    print("End of run monitor")
    return False

def service_monitor(event, context):
    try:
        if not run_monitor():
            alert_failed("Connection fail: returned false")
    except BaseException as e:
        alert_failed("Connection fail: {}".format(e))
        raise e
    except:
        alert_failed("Connection fail: non-BaseException?")
        raise

if __name__ == "__main__":
    service_monitor((),())




def makeFakeBoto():
    class FakeBoto3:
        class session:
            class Session:
                all_sessions = list()
                def __init__(self, region_name, profile_name):
                    FakeBoto3.session.Session.all_sessions.append(self)
                    self.region_name = region_name
                    self.profile_name = profile_name
                def client(self, service):
                    self.service = service
                    return self
                def send_email(self, Source, Destination, Message):
                    self.send_email = {"src": Source, "dest": Destination,
                        "msg": Message}
                    return "Fake email sent"
    return FakeBoto3

class TestClass(unittest.TestCase):
    def test_with_200_expect_200(self):
        global boto3, SETTINGS

        fake_set = {
            "region": "fake_reg",
            "profile": "fake_prof",
            "from_addr": "from@from.com",
            "to_addr": "to@to.com",
            "url": "https://google.com/",
            "expect": 200,
        }

        boto3 = makeFakeBoto()
        SETTINGS = fake_set

        service_monitor((),())

        self.assertEqual(len(boto3.session.Session.all_sessions), 0)

    def test_with_200_expect_400(self):
        global boto3, SETTINGS

        fake_set = {
            "region": "fake_reg",
            "profile": "fake_prof",
            "from_addr": "from@from.com",
            "to_addr": "to@to.com",
            "url": "https://google.com/",
            "expect": 400,
        }

        boto3 = makeFakeBoto()
        SETTINGS = fake_set

        with self.assertRaises(RuntimeError):
            service_monitor((),())

        self.assertEqual(len(boto3.session.Session.all_sessions), 1)
        
        out_sess = boto3.session.Session.all_sessions[0]

        self.assertEqual(out_sess.region_name, fake_set["region"])
        self.assertEqual(out_sess.profile_name, fake_set["profile"])
        self.assertEqual(out_sess.service, "ses")
        self.assertEqual(out_sess.send_email["src"], fake_set["from_addr"])
        self.assertEqual(out_sess.send_email["dest"]["ToAddresses"], [fake_set["to_addr"]])
        print(out_sess.send_email["msg"])

    def test_with_404_expect_404(self):
        global boto3, SETTINGS

        fake_set = {
            "region": "fake_reg",
            "profile": "fake_prof",
            "from_addr": "from@from.com",
            "to_addr": "to@to.com",
            "url": "https://google.com/WEKNenWENWEweklj",
            "expect": 404,
        }

        boto3 = makeFakeBoto()
        SETTINGS = fake_set

        service_monitor((),())

        self.assertEqual(len(boto3.session.Session.all_sessions), 0)

    def test_with_404_expect_300(self):
        global boto3, SETTINGS

        fake_set = {
            "region": "fake_reg",
            "profile": "fake_prof",
            "from_addr": "from@from.com",
            "to_addr": "to@to.com",
            "url": "https://google.com/WEKNenWENWEweklj",
            "expect": 300,
        }

        boto3 = makeFakeBoto()
        SETTINGS = fake_set

        with self.assertRaises(urllib.error.HTTPError):
            service_monitor((),())

        self.assertEqual(len(boto3.session.Session.all_sessions), 1)
        
        out_sess = boto3.session.Session.all_sessions[0]

        self.assertEqual(out_sess.region_name, fake_set["region"])
        self.assertEqual(out_sess.profile_name, fake_set["profile"])
        self.assertEqual(out_sess.service, "ses")
        self.assertEqual(out_sess.send_email["src"], fake_set["from_addr"])
        self.assertEqual(out_sess.send_email["dest"]["ToAddresses"], [fake_set["to_addr"]])
        print(out_sess.send_email["msg"])

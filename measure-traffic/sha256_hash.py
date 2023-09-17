#!/usr/bin/python3
import getpass
import hashlib
import os
import sys

def write_passwd_hash_to_file(filename):
    passwd0 = getpass.getpass(prompt="Password: ")
    passwd1 = getpass.getpass(prompt="Retype the same password: ")
    if passwd0 == passwd1:
        hsh = hashlib.sha256(bytes(passwd0, "ascii"))
        hex_digest = hsh.hexdigest()
        fd = os.open(filename, os.O_CREAT|os.O_WRONLY|os.O_TRUNC, 0o400)
        os.write(fd, bytes(hex_digest, "ascii"))
        os.close(fd)
        return 1                # OK
    else:
        print("passwords did not match", file=sys.stderr)
        return 0                # NG

def main():
    print("This program computes sha256 digest of the password you type and save it to .passwd_hash file")
    if write_passwd_hash_to_file(".passwd_hash"):
        print("Password saved to .passwd_hash")
        return 0
    else:
        return 1

sys.exit(main())

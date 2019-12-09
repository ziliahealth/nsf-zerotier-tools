#!/usr/bin/env python3

from zerotier import client as ztclient
import json
import sys
import argparse
import inspect

def main():
    # The best way to get the new-member-id(nodeid) is to use
    # $ zerotier-cli info
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', action="store", type=str)
    parser.add_argument('--network-id', action="store", type=str)
    parser.add_argument('--new-member-id', action="store", type=str)
    parser.add_argument('--description', action="store", type=str)
    args = parser.parse_args()
    print( len(vars(args)) * 2 + 1)
    print( len(sys.argv))

    # sys.argv - 1 = argument minus the binary name
    # args * 2 = argument name plus the actual arg
    if ( len(sys.argv) - 1 ) < ( len(vars(args)) * 2 ):
        parser.print_help(sys.stderr)
        sys.exit(1)

    token = args.token

    # create client and set the authentication header
    client = ztclient.Client()
    client.set_auth_header("Bearer " + token)

    network = client.network.getNetwork(args.network_id).json()
    members = client.network.listMembers(network['id']).json()
    print(members)


    # add new member to the network and authorize
    network['config'].update({'authorized': True})
    client.network.updateMember(network, args.new_member_id, network['id'])

if __name__ == "__main__":
    main()
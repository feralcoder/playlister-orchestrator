#!/bin/bash
PLAYLISTER_SETUP_SOURCE="${BASH_SOURCE[0]}"
PLAYLISTER_SETUP_DIR=$( realpath `dirname $PLAYLISTER_SETUP_SOURCE` )

. ~/CODE/venvs/kolla-ansible/bin/activate
. /etc/kolla/admin-openrc.sh
KEY=~/.ssh/keypair.cliff_admin.private

openstack quota set --cores 200 --ram 512000 playlister
openstack quota set --secgroup-rules 1000 --secgroups 30 playlister


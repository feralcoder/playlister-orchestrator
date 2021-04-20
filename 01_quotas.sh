#!/bin/bash

. ~/CODE/venvs/kolla-ansible/bin/activate
. /etc/kolla/admin-openrc.sh
KEY=~/.ssh/keypair.cliff_admin.private

openstack quota set --cores 200 --ram 512000 playlister
openstack quota set --secgroup-rules 1000 --secgroups 30 playlister


#!/bin/bash
PLAYLISTER_SETUP_SOURCE="${BASH_SOURCE[0]}"
PLAYLISTER_SETUP_DIR=$( realpath `dirname $PLAYLISTER_SETUP_SOURCE` )

KOLLA_SETUP_DIR=~/CODE/feralcoder/kolla-ansible/admin-scripts/

. $PLAYLISTER_SETUP_DIR/common.sh
new_venv playlister
use_venv playlister

. $PLAYLISTER_SETUP_DIR/playlister-openrc.sh
KEYPATH=~/.ssh/keypair.cliff_admin.private
KEYNAME=cliff_admin

openstack keypair create cliff_admin --public-key $KOLLA_SETUP_DIR/../files/keypair.cliff_admin.public


openstack server list

#openstack project create --domain default --description "playlister" playlister
#
#
##openstack user create --domain default --password $PASS playlister
#openstack user create --domain default --password-prompt playlister

# heat_stack_user  role actually breaks ability to see heat stacks...
#for ROLE in load-balancer_global_observer  load-balancer_observer heat_stack_owner load-balancer_admin _member_  load-balancer_member load-balancer_quota_admin reader member admin ; do 
#  openstack role add --user playlister --project playlister $ROLE
#done



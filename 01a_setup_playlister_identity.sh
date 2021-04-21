#!/bin/bash -x
FERALSTACK_SETUP_SOURCE="${BASH_SOURCE[0]}"
FERALSTACK_SETUP_DIR=$( realpath `dirname $FERALSTACK_SETUP_SOURCE` )


. ~/CODE/venvs/kolla-ansible/bin/activate
. /etc/kolla/admin-openrc.sh
KEYPATH=~/.ssh/keypair.cliff_admin.private
KEYNAME=cliff_admin



openstack project create --domain default --description "playlister" playlister


#openstack user create --domain default --password $PASS playlister
openstack user create --domain default --password-prompt playlister

# heat_stack_user  role actually breaks ability to see heat stacks...
for ROLE in load-balancer_global_observer  load-balancer_observer heat_stack_owner load-balancer_admin _member_  load-balancer_member load-balancer_quota_admin reader member admin ; do 
  openstack role add --user playlister --project playlister $ROLE
done



#!/bin/bash
PLAYLISTER_SETUP_SOURCE="${BASH_SOURCE[0]}"
PLAYLISTER_SETUP_DIR=$( realpath `dirname $PLAYLISTER_SETUP_SOURCE` )
KOLLA_SETUP_DIR=~/CODE/feralcoder/kolla-ansible

. $PLAYLISTER_SETUP_DIR/common.sh

echo "ENTER PLAYLISTER USER PASSWORD:"
read -sr OS_PASSWORD_INPUT

new_venv playlister
use_venv playlister

sudo dnf install -y jq


sed "s/__PASSWORD__/$OS_PASSWORD_INPUT/g" $PLAYLISTER_SETUP_DIR/playlister-openrc.sh.template > $PLAYLISTER_SETUP_DIR/playlister-openrc.sh
chmod 700 $PLAYLISTER_SETUP_DIR/playlister-openrc.sh


KEYPATH=~/.ssh/keypair.cliff_admin.private
KEYNAME=cliff_admin


# Assume if file doesn't exist, we're not on kolla-ansible controller and identity portion has already been run...
[[ -d $KOLLA_SETUP_DIR ]] && {
  use_venv kolla-ansible
  . /etc/kolla/admin-openrc.sh

  PLAYLISTER_USER=`openstack user list | grep -v '\-\-\-\-\| Name ' | grep ' playlister '`
  [[ $PLAYLISTER_USER != "" ]] && openstack user create --domain default --password $OS_PASSWORD_INPUT playlister

  openstack keypair create cliff_admin --public-key $KOLLA_SETUP_DIR/../files/keypair.cliff_admin.public

  openstack project create --domain default --description "playlister" playlister
  #openstack user create --domain default --password-prompt playlister

  # heat_stack_user  role actually breaks ability to see heat stacks...
  for ROLE in load-balancer_global_observer  load-balancer_observer heat_stack_owner load-balancer_admin _member_  load-balancer_member load-balancer_quota_admin reader member admin ; do 
    openstack role add --user playlister --project playlister $ROLE
  done
}


use_venv playlister
. $PLAYLISTER_SETUP_DIR/playlister-openrc.sh

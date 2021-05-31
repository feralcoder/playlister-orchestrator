#!/bin/bash
PLAYLISTER_SETUP_SOURCE="${BASH_SOURCE[0]}"
PLAYLISTER_SETUP_DIR=$( realpath `dirname $PLAYLISTER_SETUP_SOURCE` )

. $PLAYLISTER_SETUP_DIR/common.sh
[ "${BASH_SOURCE[0]}" -ef "$0" ]  || { echo "Don't source this script!  Run it."; return 1; }

use_venv playlister

. /etc/kolla/admin-openrc.sh
KEY=~/.ssh/keypair.cliff_admin.private

source_host_control_scripts       || fail_exit "source_host_control_scripts"

ANSIBLE_CONTROLLER=dmb

setup_playlister_cephx_users () {
  CEPH_MON=`echo "$CEPH_MON_HOSTS" | tr ' ' '\n' | head -n 1`                                                                                     || return 1
  MON_CONTAINER=`ssh_control_run_as_user root "docker container list" $CEPH_MON | grep ' ceph-mon-' | awk '{print $1}'`                           || return 1
  MGR_CONTAINER=`ssh_control_run_as_user root "docker container list" $CEPH_MON | grep ' ceph-mgr-' | awk '{print $1}'`                           || return 1
  SHARE_CONTAINER=manila_share

  # CLIENT PLAYLISTER (manila)
  ssh_control_run_as_user root "docker exec $SHARE_CONTAINER ceph --name=client.manila --keyring=/etc/ceph/ceph.client.manila.keyring auth get-or-create client.playlister_columnstore -o /tmp/ceph.client.playlister_columnstore.keyring" $CEPH_MON    || return 1
  ssh_control_run_as_user root "docker cp $SHARE_CONTAINER:/tmp/ceph.client.playlister_columnstore.keyring /tmp/" $CEPH_MON    || return 1
  ssh_control_run_as_user cliff "ssh_control_sync_as_user root /tmp/ceph.client.playlister_columnstore.keyring /etc/ceph/ $ANSIBLE_CONTROLLER" $CEPH_MON     || return 1
#  # CLIENT PLAYLISTER (manila)
#  ssh_control_run_as_user root "docker exec $MGR_CONTAINER ceph auth get-or-create client.playlister_columnstore -o /etc/ceph/ceph.client.playlister_columnstore.keyring" $CEPH_MON    || return 1
#  ssh_control_run_as_user cliff "ssh_control_sync_as_user root /etc/ceph/ceph.client.playlister_columnstore.keyring /etc/ceph/ $ANSIBLE_CONTROLLER" $CEPH_MON     || return 1
}



setup_manila_shares () {
  manila create CEPHFS 100 --name playlister_columnstore  --share-type generic_with_snapshot
  # USER MUST BE CREATED HERE - and then key can be fetched and distributed
  manila access-allow playlister_columnstore cephx playlister_columnstore

  sudo cp $PLAYLISTER_SETUP_DIR/files/ceph-playlister.conf /etc/ceph/
  manila share-export-location-list playlister_columnstore | grep -v '\-\-\-\-\|Path' | awk '{print $4}' | sed 's|.*\:/|/|g' | sudo tee /etc/ceph/manila-playlister-share-path
}


install_prereqs () {
  sudo yum install -y centos-release-ceph-nautilus epel-release
  sudo yum install -y ceph-fuse
}


SUDO_PASS_FILE=`admin_control_get_sudo_password`    || fail_exit "admin_control_get_sudo_password"
install_prereqs                            || fail_exit "install_prereqs"
setup_manila_shares                       || fail_exit "setup_manila_shares"
setup_playlister_cephx_users                       || fail_exit "setup_playlister_cephx_users"

[[ $SUDO_PASS_FILE == ~/.password ]]                || rm $SUDO_PASS_FILE


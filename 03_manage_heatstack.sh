#!/bin/bash
PLAYLISTER_SOURCE="${BASH_SOURCE[0]}"
PLAYLISTER_DIR=$( realpath `dirname $PLAYLISTER_SOURCE` )
TEMPLATE_DIR=$PLAYLISTER_DIR/playlister.heat/

. $PLAYLISTER_DIR/common.sh
[ "${BASH_SOURCE[0]}" -ef "$0" ]  || { echo "Don't source this script!  Run it."; return 1; }

use_venv playlister               || fail_exit "use_venv kolla-ansible"
. $PLAYLISTER_SETUP_DIR/playlister-openrc.sh

ANSIBLE_CONTROLLER=dmb

STACK_NAME=$1
[[ $STACK_NAME != "" ]] || { echo "STACK_NAME undefined!"; exit; }



rename_servers () {
  SERVER_LINES=`openstack server list --all | grep -v '\-\-\-\| Name ' | grep " ${STACK_NAME}[_-]"`
  FE_LINES=`echo "$SERVER_LINES" | grep " ${STACK_NAME}[_-]fe[ -]"`
  OLAP_LINES=`echo "$SERVER_LINES" | grep " ${STACK_NAME}[_-]olap[ -]"`
  OLTP_LINES=`echo "$SERVER_LINES" | grep " ${STACK_NAME}[_-]oltp[ -]"`

  ID_IP_PAIRS=$(while read -r LINE; do
    ID=`echo $LINE | awk '{print $2}'`
    IP=`echo $LINE | awk '{print $8}' | awk -F'=' '{print $2}'`
    echo $ID:$IP
#  done < <(printf '%s\n' "$FE_LINES\n$OLAP_LINES\n$OLTP_LINES"))

  for PAIR in $ID_IP_PAIRS; do
    ID=`echo $PAIR | awk -F':' '{print $1}'`
    IP=`echo $PAIR | awk -F':' '{print $2}'`
    ssh-keygen -R $IP
    HOSTNAME=`ssh -J admin1 -o "StrictHostKeyChecking no" -i ~/.ssh/keypair.cliff_admin.private -l centos $IP hostname -s`
    until [[ $? == 0 ]]; do
      echo "Failed to ssh into $IP.  Will try again in 15s..."
      sleep 15
      HOSTNAME=`ssh -J admin1 -o "StrictHostKeyChecking no" -i ~/.ssh/keypair.cliff_admin.private -l centos $IP hostname -s`
    done
    echo "Renaming $ID to $HOSTNAME"
    openstack server set --name $HOSTNAME $ID

    echo "Resetting $HOSTNAME.novalocal on puppetmaster"
    ssh root@puppetmaster "/opt/puppetlabs/bin/puppetserver ca clean --certname $HOSTNAME.novalocal"
    # PUPPET PROBABLY RAN AND BJORKED ITSELF...
    ssh -J admin1 -o "StrictHostKeyChecking no" -i ~/.ssh/keypair.cliff_admin.private -l centos $IP "sudo /opt/puppetlabs/bin/puppet resource service puppet ensure=stopped"
    ssh -J admin1 -o "StrictHostKeyChecking no" -i ~/.ssh/keypair.cliff_admin.private -l centos $IP "sudo /usr/bin/rm -rf /etc/puppetlabs/puppet/ssl/"
    ssh -J admin1 -o "StrictHostKeyChecking no" -i ~/.ssh/keypair.cliff_admin.private -l centos $IP "sudo /opt/puppetlabs/bin/puppet agent --test"
  done
}

rename_servers

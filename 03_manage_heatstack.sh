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
  FE_LINES=`echo "$SERVER_LINES" | grep " ${STACK_NAME}_fe[ -]"`
  OLAP_LINES=`echo "$SERVER_LINES" | grep " ${STACK_NAME}_olap[ -]"`
  OLTP_LINES=`echo "$SERVER_LINES" | grep " ${STACK_NAME}_oltp[ -]"`

  ID_IP_PAIRS=$(while read -r LINE; do
    ID=`echo $LINE | awk '{print $2}'`
    IP=`echo $LINE | awk '{print $8}' | awk -F'=' '{print $2}'`
    echo $ID:$IP
  done < <(printf '%s\n' "$SERVER_LINES"))

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
  done
}
#
#gather_details () {
#  STACK_ID=$(openstack stack list | grep " $STACK_NAME " | awk '{print $2}')
#  STACK_LIST=$(openstack stack list --nested | grep $STACK_NAME) || return 1
#  RESOURCE_LIST=$(openstack stack resource list $STACK_ID --nested-depth 10) || return 1
#  OLAP_STACK_NAMES=$(echo "$RESOURCE_LIST" | grep " olap_backend " | awk '{print $12}')
#  OLTP_STACK_NAMES=$(echo "$RESOURCE_LIST" | grep " oltp_backend " | awk '{print $12}')
#  OLAP_STACK_IDS=$(for NAME in $OLAP_STACK_NAMES; do
#    echo "$STACK_LIST" | grep $NAME | awk '{print $2}'
#  done)
#  OLTP_STACK_IDS=$(for NAME in $OLTP_STACK_NAMES; do
#    echo "$STACK_LIST" | grep $NAME | awk '{print $2}'
#  done)
#  OLAP_IPS=$(for ID in $OLAP_STACK_IDS; do
#    openstack stack output show $ID server_ip -f json | jq '.["output_value"]' | sed 's/"//g' || return 1
#  done)
#  OLTP_IPS=$(for ID in $OLTP_STACK_IDS; do
#    openstack stack output show $ID server_ip -f json | jq '.["output_value"]' | sed 's/"//g' || return 1
#  done)
#}
#
#print_details () {
#  echo "OLAP_STACK_NAMES:" $OLAP_STACK_NAMES
#  echo "OLTP_STACK_NAMES:" $OLTP_STACK_NAMES
#  echo "OLAP_STACK_IDS:" $OLAP_STACK_IDS
#  echo "OLTP_STACK_IDS:" $OLTP_STACK_IDS
#  echo "OLAP_STACK_IPS:" $OLAP_STACK_IPS
#  echo "OLTP_STACK_IPS:" $OLTP_STACK_IPS
#}

rename_servers
#gather_details
#print_details

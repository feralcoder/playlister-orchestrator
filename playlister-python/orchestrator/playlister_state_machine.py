import os
import subprocess
import logging, sys
from multiprocessing import Pool
from .playlister_cluster import PlaylisterCluster
from .puppet_master_files import PuppetMasterFiles
from .node_manager import NodeManager


class PlaylisterStateMachine ():
  def __init__(self, name, manifest, script_dir, reinitialize=True):
    self.manifest = manifest
    self.playlister_cluster = PlaylisterCluster(name, reinitialize)
    self.puppet_master_files = PuppetMasterFiles(manifest.puppetmaster)
    self.node_managers = {}
    self.script_dir = script_dir
    self.cache_dir = "{0}/cache".format(script_dir)

    self.clear_cluster()
    if reinitialize:
      stack_details = self.get_stack_details_from_openstack()
      self.playlister_cluster.parse_openstack_details(stack_details)
      self.create_cluster()
    else:
      stack_details = self.get_stack_details_from_manifest()
      self.playlister_cluster.parse_manifest_details(stack_details)
      self.create_cluster()

  def create_cluster(self):
    if not self.manifest.cluster_exists():
      self.manifest.new_cluster()
    for node_type in [ 'FE', 'OLAP', 'OLTP' ]:
      logging.debug("Generating cluster {0} nodes...".format(node_type))

      for node in self.playlister_cluster.nodes[node_type]:
        logging.info("Setting up {0} NodeManager...".format(node['name']))
        self.node_managers[node['name']] = NodeManager(self.manifest.cluster_path, node)
        logging.info("Getting node {0} state...".format(node['name']))
        node_state = self.node_managers[node['name']].get_puppet_state()
        target_state = node_state['state']
        if target_state == "": target_state = 'initial_build'
        logging.info("Node {0} state is {1}".format(node['name'], target_state))
        logging.info("Generating {0} configs...".format(node['name']))
        node_configs = self.playlister_cluster.configure_node(node, target_state)
        logging.info("Adding {0} to manifest...".format(node['name']))
        self.manifest.configure_node(node, node_configs)
    self.manifest.write_node_list(self.playlister_cluster.nodes['FE'] + self.playlister_cluster.nodes['OLAP'] + self.playlister_cluster.nodes['OLTP'])

  def delete_cluster(self):
    elf.clear_cluster(push=True)

  def clear_cluster(self, push=False):
    if self.manifest.cluster_exists():
      node_list = self.manifest.get_node_list()
      for node in node_list:
        logging.info("Clearing {0} from manifest...".format(node['name']))
        self.remove_node(node['name'], push)
      self.manifest.write_node_list([])


  ### REFACTOR - NODE OPERATIONS
  def remove_node(self, node_name, push=False):
    self.playlister_cluster.remove_node(node_name)
    self.manifest.remove_node(node_name, push)
    if node_name in self.node_managers.keys(): del self.node_managers[node_name]

  def get_node_state(self, node):
    node_facts = self.playlister_cluster.get_configs(node)['facts']
    live_state = self.node_managers[node['name']].get_puppet_state()
    raise Exception("get_node_state not finished implemented! Node facts: {0}\nLive state: {1}".format(node_facts, live_state))
    # GET STATE FROM LIVE MACHINE
    # RETURN state = {'state':xxx, 'stage':<pre-transition|transitioning|transitioned>}

  def set_node_state(self, node, state, push=False):
    logging.info("Setting node {0} state to {1}.".format(node['name'], state))
    configs = self.playlister_cluster.configure_node(node, state)
    self.manifest.configure_node(node, configs, push)

  def set_node_state_all(self, node_type, state, push=False):
    logging.info("Setting all {0} nodes state to {1}.".format(node_type, state))
    for node in self.playlister_cluster.nodes[node_type]:
      self.set_node_state(node, state, push)

  def transition_node_state(self, node):
    logging.info("Transitioning node {0} to new state.".format(node['name']))
    self.deploy_node_configs(node)
    self.node_managers[node['name']].puppet_update()

  def transition_node_state_all(self, node_type):
    logging.info("Transitioning all {0} nodes to new state.".format(node_type))
    parallelism = 5
    with Pool(processes=parallelism) as pool:
      result = pool.map(self.transition_node_state, self.playlister_cluster.nodes[node_type])


  ### NODE OPERATIONS
  def deploy_node_configs(self, node):
    logging.info("Deploying node {0} configs to puppetmaster.".format(node['name']))
    self.manifest.deploy_node_configs(node)

  ### CLUSTER TRANSITIONS
  def install_transaction_db(self):
    self.install_galera_cluster()

  def install_analytics_db(self):
    self.install_columnstore_cluster()

  def initialize_transaction_db(self):
    self.initialize_galera_cluster()

  def initialize_analytics_db(self):
    self.initialize_columnstore_cluster()

  def restore_transaction_db(self):
    self.restore_galera_cluster()

  def restore_analytics_db(self):
    self.restore_columnstore_cluster()

  def backup_transaction_db(self):
    self.backup_galera_cluster()

  def backup_analytics_db(self):
    self.backup_columnstore_cluster()

  def start_transaction_db(self):
    self.start_galera_cluster()

  def stop_transaction_db(self):
    self.stop_galera_cluster()

  def start_analytics_db(self):
    raise Exception("start_analytics_db not yet implemented!")

  def stop_analytics_db(self):
    raise Exception("stop_analytics_db not yet implemented!")

  def deploy_playlister_code(self, parallel=False):
    self.deploy_frontend_code(parallel)



  ### FRONTEND TRANSITIONS
  def install_frontends(self):
    self.set_node_state_all('FE', 'initial_build', push=True)
    self.transition_node_state_all('FE')
    for node in self.playlister_cluster.nodes['FE']:
      node_state = self.node_managers[node['name']].get_puppet_state()
      logging.info("node {0} state: {1}".format(node['name'], node_state))
      if not (node_state['state'] == 'fc_playlister_fe_initial_build' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'fc_playlister_fe_initial_build_finished': {1}".format(node['name'], node_state))

  def install_frontend_node(self, node):
    raise Exception("install_frontend_node not yet implemented!")

  def deploy_frontend_code(self, parallel=False):
    self.set_node_state_all('FE', 'deploy', push=True)
    if parallel:
      self.transition_node_state_all('FE')
    for node in self.playlister_cluster.nodes['FE']:
      if not parallel:
        self.transition_node_state(node)
      node_state = self.node_managers[node['name']].get_puppet_state()
      logging.info("node {0} state: {1}".format(node['name'], node_state))
      if not (node_state['state'] == 'fc_playlister_fe_deploy' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'fc_playlister_fe_deploy_finished': {1}".format(node['name'], node_state))

  ### GALERA OLTP TRANSITIONS
  def install_galera_cluster(self):
    self.set_node_state_all('OLTP', 'initial_build', push=True)
    self.transition_node_state_all('OLTP')
    for node in self.playlister_cluster.nodes['OLTP']:
      node_state = self.node_managers[node['name']].get_puppet_state()
      logging.info("node {0} state: {1}".format(node['name'], node_state))
      if not (node_state['state'] == 'fc_playlister_oltp_initial_build' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'fc_playlister_oltp_initial_build_finished': {1}".format(node['name'], node_state))

  def install_galera_node(self, node):
    raise Exception("install_galera_node not yet implemented!")

  def assert_galera_cluster_stopped(self):
    for node in self.playlister_cluster.nodes['OLTP']:
      logging.info("Checking galera service state on {0}".format(node['name']))
      logging.info("/usr/bin/systemctl status mariadb | grep Active | grep 'inactive\|failed\|dead'")
      result = self.node_managers[node['name']].host_commander.run("/usr/bin/systemctl status mariadb | grep Active | grep 'inactive\|failed\|dead'", user='root')
      if not result[0] == 0:
        raise Exception("MariaDB is not inactive, failed, or dead on host {0}: {1}".format( node['name'], result[2]))

  def identify_latest_galera_node(self):
    seqnos = {}
    for node in self.playlister_cluster.nodes['OLTP']:
      logging.info("Checking galera state on {0}".format(node['name']))
      logging.info("/usr/bin/grep seqno /cephfs-data/{0}/galera/{1}.novalocal/grastate.dat | awk '{{print $2}}'".format(self.playlister_cluster.cluster_data['CLUSTER_NAME'], node['name']))
      seqno_result = self.node_managers[node['name']].host_commander.run("/usr/bin/grep seqno /cephfs-data/{0}/galera/{1}.novalocal/grastate.dat | awk '{{print $2}}'".format(self.playlister_cluster.cluster_data['CLUSTER_NAME'], node['name']), user='root')
      if seqno_result[0] == 0:
        try:
          seqno = int(seqno_result[1].rstrip())
          if not seqno == -1:
            logging.info("Galera sequence number for {0}: {1}".format(node['name'], seqno))
            seqnos[seqno] = node['name']
        except ValueError as e:
          logging.info("Could not get galera sequence number from {0}: {1}\n{2}".format(node['name'], seqno_result, e))
    logging.info("seqno map: {0}".format(seqnos))
    logging.info("seqno keys: {0}".format(sorted(seqnos.keys())))
    if seqnos:
      leader_name = seqnos[sorted(seqnos.keys())[-1]]
      return list(filter(lambda x: (x['name'] == leader_name), self.playlister_cluster.nodes['OLTP']))[0]
    else:
      return None

  def preinitialize_galera_cluster(self):
    self.set_node_state_all('OLTP', 'preinitialize', push=True)
    self.transition_node_state_all('OLTP')
    for node in self.playlister_cluster.nodes['OLTP']:
      node_state = self.node_managers[node['name']].get_puppet_state()
      logging.info("node {0} state: {1}".format(node['name'], node_state))
      if not (node_state['state'] == 'fc_playlister_oltp_preinitialize' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'fc_playlister_oltp_preinitialize_finished': {1}".format(node['name'], node_state))

  def initialize_galera_cluster(self):
    self.stop_galera_cluster()
    leader_node = self.identify_latest_galera_node()
    if not leader_node:
      leader_index = 0
      leader_node = self.playlister_cluster.nodes['OLTP'][0]
      logging.info("No suitable leader found, arbitrarily choosing index 0")
    logging.info("Primary OLTP node is {0}, index {1}".format(leader_node['name'], leader_index))
    self.preinitialize_galera_cluster()

    self.start_galera_leader_node(leader_node)
    self.join_galera_secondary_nodes(self.playlister_cluster.nodes['OLTP'][0:leader_index])
    self.join_galera_secondary_nodes(self.playlister_cluster.nodes['OLTP'][leader_index+1:])

  def start_galera_leader_node(self, node):
    self.set_node_state(node, 'start_leader_node', push=True)
    self.transition_node_state(node)
    node_state = self.node_managers[node['name']].get_puppet_state()
    logging.info("node {0} state: {1}".format(node['name'], node_state))
    if not (node_state['state'] == 'fc_playlister_oltp_start_leader_node' and node_state['transition'] == 'finished'):
      raise Exception("Node {0} has not reached 'fc_playlister_oltp_start_leader_node_finished': {1}".format(node['name'], node_state))

  def start_galera_cluster(self):
    self.assert_galera_cluster_stopped()
    primary_node = self.identify_latest_galera_node()
    if not primary_node:
      raise Exception("No suitable galera leader found!")
    primary_index = self.playlister_cluster.nodes['OLTP'].index(primary_node)
    logging.info("Primary OLTP node is {0}, index {1}".format(primary_node['name'], primary_index))

    self.initialize_galera_primary_node(primary_node)
    self.join_galera_secondary_nodes(self.playlister_cluster.nodes['OLTP'][0:primary_index])
    self.join_galera_secondary_nodes(self.playlister_cluster.nodes['OLTP'][primary_index+1:])

  def join_galera_secondary_nodes(self, nodes):
    for node in nodes:
      self.set_node_state(node, 'join', push=True)
      self.transition_node_state(node)
      node_state = self.node_managers[node['name']].get_puppet_state()
      logging.info("node {0} state: {1}".format(node['name'], node_state))
      if not (node_state['state'] == 'fc_playlister_oltp_join' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'fc_playlister_oltp_join_finished': {1}".format(node['name'], node_state))

  def stop_galera_cluster(self):
    for node in self.playlister_cluster.nodes['OLTP']:
      self.set_node_state(node, 'stop', push=True)
      self.transition_node_state(node)
      node_state = self.node_managers[node['name']].get_puppet_state()
      logging.info("node {0} state: {1}".format(node['name'], node_state))
      if not (node_state['state'] == 'fc_playlister_oltp_stop' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'fc_playlister_oltp_stop_finished': {1}".format(node['name'], node_state))

  def stop_galera_node(self, node):
    raise Exception("stop_galera_node not yet implemented!")

  def restore_galera_cluster(self):
    raise Exception("restore_galera_cluster not yet implemented!")

  def restore_galera_primary_node(self, node):
    raise Exception("restore_galera_primary_node not yet implemented!")

  def backup_galera_cluster(self):
    raise Exception("backup_galera_cluster not yet implemented!")

  def backup_galera_primary_node(self, node):
    raise Exception("backup_galera_primary_node not yet implemented!")

  def load_galera_schema_on_node(self, node):
    raise Exception("load_galera_schema_on_node not yet implemented!")

  def use_galera_storage_on_node(self, node):
    raise Exception("use_galera_storage_on_node not yet implemented!")

  def join_galera_secondary_node(self, node):
    raise Exception("join_galera_secondary_node not yet implemented!")

  def restore_galera_secondary_node(self, node):
    raise Exception("restore_galera_secondary_node not yet implemented!")

  def backup_galera_secondary_node(self, node):
    raise Exception("backup_galera_secondary_node not yet implemented!")

  def sync_galera_node_from_primary(self, node):
    raise Exception("sync_galera_node_from_primary not yet implemented!")

  def nominalize_galera_cluster(self):
    raise Exception("nominalize_galera_cluster not yet implemented!")

  def nominalize_galera_node(self, node):
    raise Exception("nominalize_galera_node not yet implemented!")

  ### COLUMNSTORE OLAP TRANSITIONS 
  def install_columnstore_cluster(self):
    self.set_node_state_all('OLAP', 'initial_build', push=True)
    self.transition_node_state_all('OLAP')
    for node in self.playlister_cluster.nodes['OLAP']:
      node_state = self.node_managers[node['name']].get_puppet_state()
      logging.info("node {0} state: {1}".format(node['name'], node_state))
      if not (node_state['state'] == 'fc_playlister_olap_initial_build' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'fc_playlister_olap_initial_build_finished': {1}".format(node['name'], node_state))

  def install_columnstore_node(self, node):
    raise Exception("install_columnstore_node not yet implemented!")

  def initialize_columnstore_cluster(self):
    raise Exception("initialize_columnstore_cluster not yet implemented!")

  def restore_columnstore_cluster(self):
    raise Exception("restore_columnstore_cluster not yet implemented!")

  def backup_columnstore_cluster(self):
    raise Exception("backup_columnstore_cluster not yet implemented!")

  def load_columnstore_schema_on_node(self, node):
    raise Exception("load_columnstore_schema_on_node not yet implemented!")

  def use_columnstore_storage_on_node(self, node):
    raise Exception("use_columnstore_storage_on_node not yet implemented!")

  def configure_columnstore_follow_galera(self):
    raise Exception("configure_columnstore_follow_galera not yet implemented!")

  def nominalize_columnstore_cluster(self):
    raise Exception("nominalize_columnstore_cluster not yet implemented!")

  def nominalize_columnstore_node(self, node):
    raise Exception("nominalize_columnstore_node not yet implemented!")

  def stop_columnstore_cluster(self):
    raise Exception("stop_columnstore_cluster not yet implemented!")

  def stop_columnstore_node(self, node):
    raise Exception("stop_columnstore_node not yet implemented!")









  def getOLTPPrimaryNode(self):
    return self.playlister_cluster.seeds[0]

  def get_stack_details_from_manifest(self):
    print("Noop")

  def get_stack_details_from_openstack(self, force_refresh=False):
    deets_file = "{0}/{1}_deets.txt".format(self.cache_dir, self.playlister_cluster.name)
    if force_refresh:
      if os.path.exists(deets_file):
        os.remove(deets_file)
    if not os.path.exists(deets_file):
      playlister_deets = subprocess.run(["{0}/../04_stack_deets.sh".format(self.script_dir), self.playlister_cluster.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      if playlister_deets.returncode:
        print("Error gathering playlister cluster facts for {0}!".format(self.playlister_cluster.name))
        exit()
      try:
        with open("{0}/{1}_deets.txt".format(self.cache_dir, self.playlister_cluster.name), 'w') as f:
          f.write(playlister_deets.stdout.decode('ascii'))
      except IOError as e:
        print("Could not open {0}/{1}_deets.txt for writing!".format(self.cache_dir, self.playlister_cluster.name))
        print(e)
        exit()
    try:
      with open("{0}/{1}_deets.txt".format(self.cache_dir, self.playlister_cluster.name), 'r') as f:
        stack_deets = f.read()
    except IOError as e:
      print("Could not open {0}/{1}_deets.txt for reading!".format(self.cache_dir, self.playlister_cluster.name))
      print(e)
      exit()
    return stack_deets

#  def remove_node_from_puppetmaster(self, node_name):
#    self.puppet_master_files.delete("data/nodes/{0}.novalocal.yaml".format(node_name))
#    self.puppet_master_files.delete("manifests/{0}.novalocal.pp".format(node_name))
#    self.puppet_master_files.delete("site-modules/fc_playlister_be/files/dynamic_facter/{0}.novalocal.txt".format(node_name))



# FE STATES
#  initial_build
#  up
#  stopping
#  stopped

# OLTP STATES
#  initial_build
#  primary_up
#  cluster_up
#  nominal
#  stopping
#  stopped

# OLAP STATES
#  initial_build
#  cluster_up
#  following
#  nominal
#  stopping
#  stopped


#FE_VIP: 172.30.1.15
#FE_IPS: 10.254.0.158 10.254.0.216 10.254.0.245
#OLAP_VIP: 172.30.1.25
#OLAP_IPS: 10.254.0.80 10.254.0.163 10.254.0.192 10.254.0.178
#OLTP_VIP: 172.30.1.35
#OLTP_IPS: 10.254.0.37 10.254.0.56 10.254.0.199 10.254.0.200
#FE_STACK_ID: 87542638-1c35-41c8-9b9f-ae283e313cce
#FE_STACK_ID: f9b0d14a-5177-4475-ab77-e4e7c932fa33
#FE_STACK_ID: 282fc1a2-d18d-48ea-bdf1-4d28dd21fd98
#FE_STACK_NAME: playlister5-frontends-hvyfpgghytjv-c6jqtsjhzix3-4jomnesyijw7
#FE_STACK_NAME: playlister5-frontends-hvyfpgghytjv-wsuwn723qde4-2od25qxbsadw
#FE_STACK_NAME: playlister5-frontends-hvyfpgghytjv-aonqoa4y2ge4-dxbq3m2g33ok
#OLAP_STACK_ID: 2fe8a675-3cb8-4205-b09a-a1244d6a9636
#OLAP_STACK_ID: 33038159-95af-407c-a403-f89c3dbd77d9
#OLAP_STACK_ID: 83e796cc-b67e-4b5e-b7c1-45c4281f0ab9
#OLAP_STACK_ID: 645175a3-bc0d-444b-9946-9372868331d6
#OLAP_STACK_NAME: playlister5-olap_backends-mxiwfqcaux7p-5h7mgmgtvgsq-ssdhc6hrage4
#OLAP_STACK_NAME: playlister5-olap_backends-mxiwfqcaux7p-htwxqkrsxtas-ncbwqayp4pll
#OLAP_STACK_NAME: playlister5-olap_backends-mxiwfqcaux7p-smjp7gk3girk-l5oruv5fhmkc
#OLAP_STACK_NAME: playlister5-olap_backends-mxiwfqcaux7p-5ldsfo4aqpwb-yal3lhczi7qk
#OLAP_BACKEND: playlister5-olap-10-254-0-80:e0f9a215-e5f5-40ea-8fba-190ca348d4b6:10.254.0.80
#OLAP_BACKEND: playlister5-olap-10-254-0-163:4067625b-e305-43bd-9d4f-6eb63233b16a:10.254.0.163
#OLAP_BACKEND: playlister5-olap-10-254-0-192:5ffafadd-c8a9-4e92-9e9f-c62cbe4a53b6:10.254.0.192
#OLAP_BACKEND: playlister5-olap-10-254-0-178:c1bbff13-b940-446d-a795-567b8e6f3636:10.254.0.178
#OLTP_STACK_ID: cd8e17ad-a8e4-4e02-88f1-6b7030533c45
#OLTP_STACK_ID: 559a9127-73e4-4fc3-b091-9a2ad2114f41
#OLTP_STACK_ID: 6ee7ec26-53a5-47c8-bbc7-9710e23e11e9
#OLTP_STACK_ID: 49404beb-121b-4531-bcef-609480498aca
#OLTP_STACK_NAME: playlister5-oltp_backends-wtrlwx4heote-dbfcgntvp2ze-asdzkdyiadxc
#OLTP_STACK_NAME: playlister5-oltp_backends-wtrlwx4heote-2e4wiuoe6wsc-pb5xwunh2esw
#OLTP_STACK_NAME: playlister5-oltp_backends-wtrlwx4heote-ndv33v6axdu6-6ovnzi6my535
#OLTP_STACK_NAME: playlister5-oltp_backends-wtrlwx4heote-tuuv5wgk5le5-a72ouq4qzyfl
#OLTP_BACKEND: playlister5-oltp-10-254-0-37:8be336f2-c0fd-486e-9d49-4394f3418f63:10.254.0.37
#OLTP_BACKEND: playlister5-oltp-10-254-0-56:3030a28a-4da3-43ac-ba6a-ad476580c63c:10.254.0.56
#OLTP_BACKEND: playlister5-oltp-10-254-0-199:ff5e61be-265c-4891-8b06-e4b369882767:10.254.0.199
#OLTP_BACKEND: playlister5-oltp-10-254-0-200:7081985d-0a31-4dfc-89e0-e0eca9ea717f:10.254.0.200
#MANILA_SHARE_PATH: /volumes/_nogroup/e9004bf1-a0fb-4d01-b413-ae1bc8f744de/85dea32a-4cf2-467b-8309-1558a12683f3
#MANILA_KEY: AQC+WLFgK4A6MhAAwJpuLua5GZQm4x44da/sWg==
#MON_LIST: [v2:192.168.127.210:3300,v1:192.168.127.210:6789] [v2:192.168.127.212:3300,v1:192.168.127.212:6789] [v2:192.168.127.216:3300,v1:192.168.127.216:6789]

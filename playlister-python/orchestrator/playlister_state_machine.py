import os
import subprocess
from multiprocessing import Pool
from .playlister_cluster import PlaylisterCluster
from .puppet_master_files import PuppetMasterFiles


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

  def getNodeState(self, node):
    node_facts = self.playlister_cluster.get_configs(node)['facts']
    # GET STATE FROM LIVE MACHINE
    # RETURN state = {'state':xxx, 'stage':<pre-transition|transitioning|transitioned>}

  def setNodeState(self, node, state):
    print("\nSetting node {0} state to {1}.".format(node['name'], state))
    configs = self.playlister_cluster.configure_node(node, state)
    self.manifest.configure_node(node, configs)

  def setNodeStateAll(self, node_type, state):
    print("\nSetting all {0} nodes state to {1}.".format(node_type, state))
    nodes = { 'OLAP':self.olap_nodes, 'OLTP':self.oltp_nodes, 'FE':self.fe_nodes }[node_type]
    for node in nodes:
      self.setNodeState(node, state)

  def getOLTPPrimaryNode(self):
    return self.playlister_cluster.seeds[0]

  def getNodes(self, node_type):
    return { 'OLAP':self.olap_nodes, 'OLTP':self.oltp_nodes, 'FE':self.fe_nodes }[node_type]

  def remove_node(self, node_name):
    self.playlister_cluster.remove_node(node_name)
    self.manifest.remove_node(node_name)
    self.remove_node_from_puppetmaster(node_name)
    if node_name in self.node_managers.keys(): del self.node_managers[node_name]

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

  def clear_cluster(self):
    if self.manifest.cluster_exists():
      node_list = self.manifest.get_node_list()
      for node in node_list:
        print("Clearing {0} from manifest...".format(node['name']))
        self.remove_node(node['name'])
      self.manifest.write_node_list([])

  def create_cluster(self):
    if not self.manifest.cluster_exists():
      self.manifest.new_cluster()
    for node in self.playlister_cluster.backend_nodes:
      print("Generating {0} configs...".format(node['name']))
      node_configs = self.playlister_cluster.configure_node(node, 'initial_build')
      print("Adding {0} to manifest...".format(node['name']))
      self.manifest.configure_node(node, node_configs)
      self.node_managers[node['name']] = NodeManager(self.manifest.cluster_path, node)
    self.manifest.write_node_list(self.playlister_cluster.backend_nodes)

  def transitionNodeState(self, node):
    print("\nTransitioning node {0} to new state.".format(node['name']))
    self.deploy_node_configs_to_puppetmaster(node)
    self.node_managers[node['name']].puppet_update()

  def transitionNodeStateAll(self):
    print("\nTransitioning all nodes to new state.")
    parallelism = 5
    with Pool(processes=parallelism) as pool:
      result = pool.map(self.transitionNodeState, self.playlister_cluster.backend_nodes)

  def deploy_node_configs_to_puppetmaster(self, node):
    print("\nDeploying node {0} configs to puppetmaster.".format(node['name']))
    self.puppet_master_files.sync("{0}/data-{1}.yaml".format(self.manifest.cluster_path, node['name']), "data/nodes/{0}.novalocal.yaml".format(node['name']))
    self.puppet_master_files.sync("{0}/manifest-{1}.pp".format(self.manifest.cluster_path, node['name']), "manifests/{0}.novalocal.pp".format(node['name']))
    self.puppet_master_files.sync("{0}/facter-{1}.txt".format(self.manifest.cluster_path, node['name']), "site-modules/fc_playlister_be/files/dynamic_facter/{0}.novalocal.txt".format(node['name']))

  def remove_node_from_puppetmaster(self, node_name):
    self.puppet_master_files.delete("data/nodes/{0}.novalocal.yaml".format(node_name))
    self.puppet_master_files.delete("manifests/{0}.novalocal.pp".format(node_name))
    self.puppet_master_files.delete("site-modules/fc_playlister_be/files/dynamic_facter/{0}.novalocal.txt".format(node_name))



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
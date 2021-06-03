import os
import subprocess
from multiprocessing import Pool

script_dir=os.path.dirname(os.path.realpath(__file__))
cache_dir="{0}/cache".format(script_dir)
puppetmaster = 'puppetmaster.feralcoder.org'

class PlaylisterStateMachine ():
  def __init__(self, name, manifest, puppetmaster, reinitialize=True):
    self.manifest = manifest
    self.playlister_cluster = PlaylisterCluster(name, reinitialize)
    self.puppet_master_files = PuppetMasterFiles(puppetmaster)
    self.node_managers = {}

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

  def setNodeStateAll(self, state):
    print("\nSetting all nodes state to {0}.".format(state))
    for node in self.playlister_cluster.backend_nodes:
      self.setNodeState(node, state)

  def getPrimary(self):
    return self.playlister_cluster.seeds[0]

  def getNodes(self):
    return self.playlister_cluster.backend_nodes

  def remove_node(self, node_name):
    self.playlister_cluster.remove_node(node_name)
    self.manifest.remove_node(node_name)
    self.remove_node_from_puppetmaster(node_name)
    if node_name in self.node_managers.keys(): del self.node_managers[node_name]

  def get_stack_details_from_manifest(self):
    print("Noop")

  def get_stack_details_from_openstack(self, force_refresh=False):
    deets_file = "{0}/{1}_deets.txt".format(cache_dir, self.playlister_cluster.name)
    if force_refresh:
      if os.path.exists(deets_file):
        os.remove(deets_file)
    if not os.path.exists(deets_file):
      playlister_deets = subprocess.run(["{0}/../04_stack_deets.sh".format(script_dir), self.playlister_cluster.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      if playlister_deets.returncode:
        print("Error gathering playlister cluster facts for {0}!".format(self.playlister_cluster.name))
        exit()
      try:
        with open("{0}/{1}_deets.txt".format(cache_dir, self.playlister_cluster.name), 'w') as f:
          f.write(playlister_deets.stdout.decode('ascii'))
      except IOError as e:
        print("Could not open {0}/{1}_deets.txt for writing!".format(cache_dir, self.playlister_cluster.name))
        print(e)
        exit()
    try:
      with open("{0}/{1}_deets.txt".format(cache_dir, self.playlister_cluster.name), 'r') as f:
        stack_deets = f.read()
    except IOError as e:
      print("Could not open {0}/{1}_deets.txt for reading!".format(cache_dir, self.playlister_cluster.name))
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


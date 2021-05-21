import os
import subprocess
import sys
from pathlib import Path
import re
from string import Template
import json
from multiprocessing import Pool
import time







from playlister_settings import playlister_settings

stack_name = sys.argv[1]
cwd=os.getcwd()
script_dir=os.path.dirname(os.path.realpath(__file__))
cache_dir="{0}/cache".format(script_dir)
manifest_dir="{0}/puppet-manifests".format(script_dir)
puppetmaster = 'puppetmaster.feralcoder.org'

class PlaylisterDeployer ():
  def __init__(self, name, manifest):
    self.playlister_backend_state = PlaylisterStateMachine(name, manifest, puppetmaster, reinitialize=True)

  def shutdown_cassandra(self):
    self.playlister_backend_state.setNodeStateAll('stopping')
    self.playlister_backend_state.transitionNodeStateAll()
    for node in self.playlister_backend_state.playlister_cluster.backend_nodes:
      node_state = self.playlister_backend_state.node_managers[node['name']].get_puppet_state()
      print(node_state)
      if not (node_state['state'] == 'stopping' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'initial_build_finished': {1}".format(node['name'], node_state))


  def deploy_this_thing(self):
    self.playlister_backend_state.setNodeStateAll('initial_build')
    for node in self.playlister_backend_state.playlister_cluster.backend_nodes:
      self.playlister_backend_state.transitionNodeState(node)

    for node in self.playlister_backend_state.playlister_cluster.backend_nodes:
      node_state = self.playlister_backend_state.node_managers[node['name']].get_puppet_state()
      print(node_state)
      if not (node_state['state'] == 'initial_build' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'initial_build_finished': {1}".format(node['name'], node_state))

  def start_cassandra(self):
    # Nodes are ordered with primary and secondary seeds as #1 and #2 - they were selected from the first 2.
    for node in self.playlister_backend_state.playlister_cluster.backend_nodes:
      self.playlister_backend_state.setNodeState(node, 'starting')
      self.playlister_backend_state.transitionNodeState(node)
      time.sleep(10)
      node_state = self.playlister_backend_state.node_managers[node['name']].get_puppet_state()
      if not (node_state['state'] == 'starting' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'starting_finished': {1}".format(node['name'], node_state))
      self.playlister_backend_state.node_managers[node['name']].wait_for_cassandra_up()
      print("Node {0} cassandra is up!".format(node['name']))

      self.playlister_backend_state.setNodeState(node, 'started')
      self.playlister_backend_state.transitionNodeState(node)
      node_state = self.playlister_backend_state.node_managers[node['name']].get_puppet_state()
      if not (node_state['state'] == 'started' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'started_finished': {1}".format(node['name'], node_state))
      print("Node {0} started!".format(node['name']))



  def load_schema(self):
    # Nodes are ordered with primary and secondary seeds as #1 and #2 - they were selected from the first 2.
    for node in [self.playlister_backend_state.playlister_cluster.backend_nodes[0]]:
      self.playlister_backend_state.setNodeState(node, 'load_schema')
      self.playlister_backend_state.transitionNodeState(node)
      time.sleep(10)
      node_state = self.playlister_backend_state.node_managers[node['name']].get_puppet_state()
      if not (node_state['state'] == 'load_schema' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'load_schema_finished': {1}".format(node['name'], node_state))
      print("Node {0} loaded schema!".format(node['name']))
      self.playlister_backend_state.setNodeState(node, 'started')
      self.playlister_backend_state.transitionNodeState(node)
      time.sleep(10)
      node_state = self.playlister_backend_state.node_managers[node['name']].get_puppet_state()
      if not (node_state['state'] == 'started' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'started_finished': {1}".format(node['name'], node_state))
      print("Node {0} started!".format(node['name']))


  def nominalize(self):
    control_node = self.playlister_backend_state.playlister_cluster.backend_nodes[0]
    for node in self.playlister_backend_state.playlister_cluster.backend_nodes:
      node_state = self.playlister_backend_state.node_managers[control_node['name']].get_cass_node_state(node)
      if not node_state == "UN":
        raise Exception("Can't nominalize: node {0} is in state {1}!".format(node['name'], node_state))
    while True:
      repair_status = self.playlister_backend_state.node_managers[control_node['name']].get_cass_repair_status()
      if repair_status == True: break
      print("Cassandra cluster still repairing.  Sleeping.")
      time.sleep(20)
    print("Cassandra cluster has finished repairing!")

    self.playlister_backend_state.setNodeStateAll('nominal')
    self.playlister_backend_state.transitionNodeStateAll()
    for node in self.playlister_backend_state.playlister_cluster.backend_nodes:
      node_state = self.playlister_backend_state.node_managers[node['name']].get_puppet_state()
      if not (node_state['state'] == 'nominal' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'nominal_finished': {1}".format(node['name'], node_state))
      print("Node {0} cassandra is nominal!".format(node['name']))




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

class PlaylisterCluster ():
  def __init__(self, name, reinitialize=False):
    self.name = name
    self.settings = playlister_settings[self.name]
    self.configs = {}
    self.backend_nodes = []

  def parse_manifest_details(self):
    print("NOOP")

  def parse_openstack_details(self, stack_details):
    backend_nodes = []
    backend_re = re.compile('^BACKEND: (.*)')
    seed_re = re.compile('^BACKEND_SEEDS: (.*)')
    for line in stack_details.splitlines():
      match = backend_re.match(line)
      if match:
        print("Backend Line: {0}".format(match.group(1)))
        backend_nodes.append(match.group(1))
      match = seed_re.match(line)
      if match:
        print("Seed Line: {0}".format(match.group(1)))
        self.seeds = match.group(1).split(',')
    self.backend_nodes = []
    for backend in backend_nodes:
      node = {}
      (node['name'], node['id'], node['ip']) = backend.split(':')
      if [x for x in self.seeds if node['ip'] == x]:
        node['is_seed']=True
      else:
        node['is_seed']=False
      self.backend_nodes.append(node)

  def remove_node(self, node_name):
    for node in self.backend_nodes:
      if node['name'] == node_name:
        self.backend_nodes.remove(node)
    if node_name in self.configs.keys(): del self.configs[node_name]

  def configure_node(self, node, state):
    s = self.settings
    node_name = node['name']
    seeds = ','.join(self.seeds)
    with open("{0}/../files/node-data.yaml.template".format(script_dir), 'r') as f:
      data_template=Template(f.read())
    with open("{0}/../files/node-manifest.pp.template".format(script_dir), 'r') as f:
      manifest_template=Template(f.read())
    with open("{0}/../files/node-facter.txt.template".format(script_dir), 'r') as f:
      facts_template=Template(f.read())
    data_text = data_template.substitute(cluster_name=s['cluster_name'], dc=s['DC'], rack=s['rack'], package_ensure=s['package_ensure'], package=s['package'])
    manifest_text = manifest_template.substitute(node=node_name, seeds=seeds, state=state)
    facts_text = facts_template.substitute(state=state, test='test', cluster_name=s['cluster_name'], dc=s['DC'], rack=s['rack'], package_ensure=s['package_ensure'], package=s['package'])
    self.configs[node_name] = {'data':data_text, 'manifest':manifest_text, 'facts':facts_text}
    return self.configs[node_name]

  def get_node_config(self, node):
    return self.configs[node['name']]



class PuppetManifest ():
  def __init__(self, manifest_path, cluster_name, environment, puppetmaster):
    self.path = manifest_path
    self.cluster_name = cluster_name
    self.cluster_path = "{0}/{1}".format(manifest_path, cluster_name)
    self.environment = environment

  def git_pull(self):
    try:
      run_git = subprocess.run(["/usr/bin/git", "checkout", self.environment], cwd=self.path)
      if not run_git:
        raise Exception("Could not check out branch {0} in {1}".format(self.environment, self.path))
      run_git = subprocess.run(["/usr/bin/git", "pull"], cwd=self.path)
      if not run_git:
        raise Exception("Could not update {0}".format(self.path))
    except Exception as e:
      print("Failed to update puppet-manifests: {0}".format(e))
      exit()

  def new_cluster(self):
    if self.cluster_exists():
      raise Exception("Cannot create, cluster {0} already exists!".format(self.cluster_name))
    os.mkdir(self.cluster_path)
    Path("{0}/node.list".format(self.cluster_path)).touch()

  def configure_node(self, node, node_configs):
    node_name = node['name']
    with open("{0}/data-{1}.yaml".format(self.cluster_path, node_name), 'w') as f:
      f.write(node_configs['data'])
    with open("{0}/manifest-{1}.pp".format(self.cluster_path, node_name), 'w') as f:
      f.write(node_configs['manifest'])
    with open("{0}/facter-{1}.txt".format(self.cluster_path, node_name), 'w') as f:
      f.write(node_configs['facts'])

  def get_node_list(self):
    node_file = "{0}/node.list".format(self.cluster_path)
    try:
      with open(node_file, 'r') as f:
        node_lines=f.read().splitlines()
    except IOError as e:
      print("Could not read nodes from {0}!".format(node_file))
      print(e)
      exit()
    nodes = []
    for line in node_lines:
      nodes.append(json.loads(line))
    return nodes

  def write_node_list(self, node_list):
    node_file = "{0}/node.list".format(self.cluster_path)
    try:
      with open(node_file, 'w') as f:
        for node in node_list:
          json.dump(node, f)
          f.write('\n')
    except IOError as e:
      print("Could not write nodes to {0}!".format(node_file))
      print(e)
      exit()

  def cluster_exists(self):
    return os.path.isdir(self.cluster_path)

  def remove_node(self, node_name):
    print("Removing manifest node {0}".format(node_name))
    for file in ["{0}/data-{1}.yaml".format(self.cluster_path, node_name), "{0}/manifest-{1}.pp".format(self.cluster_path, node_name), "{0}/facter-{1}.txt".format(self.cluster_path, node_name)]:
      if os.path.isfile(file): os.remove(file)
    nodes = self.get_node_list()
    for node in nodes:
      if node['name'] == node_name: nodes.remove(node)
    self.write_node_list(nodes)


class NodeManager ():
  def __init__(self, cluster_config_path, node):
    self.cluster_config_path = cluster_config_path
    self.node = node
    self.host_commander = HostCommander('cliff', '/home/cliff/.ssh/id_rsa')
    self.host_commander.reset_fingerprint(self.node['ip'])

  def puppet_update(self):
    puppet_result = self.host_commander.run(self.node['ip'], "cat ~/.password | sudo -S ls > /dev/null; sudo /opt/puppetlabs/bin/puppet agent --test")
    print(puppet_result[1])
    if puppet_result[2]: print("STDERR OUTPUT:\n{0}".format(puppet_result[2]))
    print("Puppet Agent returned code: {0}".format(puppet_result[0]))
    if puppet_result[0] == 1:
      raise Exception("puppet agent failed!")

  def get_puppet_state(self):
    print("\nGetting puppet state on node {0}.".format(self.node['name']))
    state_result = self.host_commander.run(self.node['ip'], "ls /etc/puppetlabs/fc_playlister_be_state/")
    state_segments = state_result[1].rstrip().split('_')
    return({ 'state':'_'.join(state_segments[:-1]), 'transition':state_segments[-1] })

  def start_cass_full_repair(self):
    nodetool_repair_out = self.host_commander.run(self.node['ip'], "/usr/bin/nodetool repair --full")
    if nodetool_repair_out[0]:
      print("Nodetool repair returned nonzero exit code.  This may not be a problem - please investigate.")
#      raise Exception("Nodetool error getting node state for {0}".format(node['ip']))
    return nodetool_repair_out[1].rstrip()

  def get_cass_repair_status(self):
    # True = finished, False = running
    calculation_done = repair_done = False

    repair_compaction_status = self.host_commander.run(self.node['ip'], "/usr/bin/nodetool compactionstats")
    if repair_compaction_status[0]:
      raise Exception("Nodetool error getting compactionstats!")
    if not re.match(r'pending tasks: 0$', repair_compaction_status[1]):
      print("Cassandra is still calculating repair differences!")
      print(repair_compaction_status[1])
    else:
      calculation_done = True

    repair_netstats_status = self.host_commander.run(self.node['ip'], "/usr/bin/nodetool netstats")
    if repair_netstats_status[0]:
      raise Exception("Nodetool error getting netstats!")
    if not re.search(r'Mismatch .Blocking.: 0$', repair_netstats_status[1], re.M) or not re.search(r'Mismatch .Background.: 0$', repair_netstats_status[1], re.M):
      print("Cassandra is still performing repairs!")
      print(repair_netstats_status[1])
    else:
      repair_done = True

    if calculation_done == True and repair_done == True:
      print("Nodetool repair is fisihed!")
      return True
    else:
      return False

  def get_cass_node_state(self, node):
    nodetool_test = self.host_commander.run(self.node['ip'], "/usr/bin/nodetool status | grep ' {0} ' | awk '{{print $1}}'".format(node['ip']))
    if nodetool_test[0]:
      raise Exception("Nodetool error getting node state for {0}".format(node['ip']))
    return nodetool_test[1].rstrip()

  def wait_for_cassandra_up(self):
    #attempts = 2
    attempts = 120
    sleep = 10
    attempt = 0
    nodetool_test = [None, None, None]
    while not nodetool_test[1] == "UN\n":
      if attempt == attempts: raise Exception("Timed out waiting for node {0} to reach 'UN' state!".format(node['ip']))
      attempt = attempt + 1
      nodetool_test = self.host_commander.run(self.node['ip'], "/usr/bin/nodetool status | grep ' {0} ' | awk '{{print $1}}'".format(self.node['ip']))
      time.sleep(sleep)




class PuppetMasterFiles ():
  def __init__(self, puppetmaster, code_dir='/etc/puppetlabs/code/environments/production'):
    self.puppetmaster = puppetmaster
    self.code_dir = code_dir

  def sync(self, source_file, dest_file):
    sync_result = subprocess.run(["/usr/bin/rsync", source_file, "root@{0}".format(self.puppetmaster) + ":{0}/{1}".format(self.code_dir, dest_file)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  def delete(self, dest_file):
    delete_result = subprocess.run(["/usr/bin/ssh", "root@{0}".format(self.puppetmaster),  "rm {0}/{1}".format(self.code_dir, dest_file)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class HostCommander ():
  def __init__(self, user, key_path):
    self.user = user
    self.key_path = key_path

  def reset_fingerprint(self, host):
    ssh_result = subprocess.run(["/usr/bin/ssh-keygen", "-R host"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  def run(self, host, command):
    ssh_result = subprocess.run(["/usr/bin/ssh", "-J admin1", "-o StrictHostKeyChecking no", "{0}@{1}".format(self.user, host), "{0}".format(command)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #ssh_result = subprocess.run(["/usr/bin/ssh", "-J admin1", "-o StrictHostKeyChecking no", "-i {0}".format(self.key_path), "{0}@{1}".format(self.user, host), "{0}".format(command)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if ssh_result:
      return [ssh_result.returncode, ssh_result.stdout.decode('ascii'), ssh_result.stderr.decode('ascii')]
    else:
      raise Exception("error running {0} on {1}".format(command, host))



manifest = PuppetManifest(manifest_dir, stack_name, "production", puppetmaster)
manifest.git_pull()
playlister_deployer = PlaylisterDeployer(stack_name, manifest)
#playlister_deployer.deploy_this_thing()
playlister_deployer.start_cassandra()
#playlister_deployer.load_schema()
#playlister_deployer.nominalize()
#playlister_deployer.shutdown_cassandra()

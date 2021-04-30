import os
import subprocess
import sys
from pathlib import Path
import re
from string import Template

from playlister_settings import playlister_settings

stack_name = sys.argv[1]
cwd=os.getcwd()
script_dir=os.path.dirname(os.path.realpath(__file__))
cache_dir="{0}/cache".format(script_dir)
manifest_dir="{0}/puppet-manifests".format(script_dir)
puppetmaster = 'puppetmaster.feralcoder.org'

class PlaylisterCluster ():
  def __init__(self, name, reinitialize=False):
    self.name = name
    self.manifest_name = "playlister_{0}".format(self.name)
    if reinitialize:
      self.stack_details = self.get_stack_details_from_openstack()
    else:
      self.stack_details = self.get_stack_details_from_manifest()
    self.parse_openstack_details()
    self.settings = playlister_settings[self.name]

  def get_stack_details_from_manifest(self):
    print("Noop")

  def get_stack_details_from_openstack(self, force_refresh=False):
    deets_file = "{0}/{1}_deets.txt".format(cache_dir, stack_name)
    if force_refresh:
      if os.path.exists(deets_file):
        os.remove(deets_file)
    if not os.path.exists(deets_file):
      playlister_deets = subprocess.run(["{0}/../04_stack_deets.sh".format(script_dir), stack_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      if playlister_deets.returncode:
        print("Error gathering playlister cluster facts for {0}!".format(stack_name))
        exit()
      try:
        with open("{0}/{1}_deets.txt".format(cache_dir, stack_name), 'w') as f:
          f.write(playlister_deets.stdout.decode('ascii'))
      except IOError as e:
        print("Could not open {0}/{1}_deets.txt for writing!".format(cache_dir, stack_name))
        print(e)
        exit()
    try:
      with open("{0}/{1}_deets.txt".format(cache_dir, stack_name), 'r') as f:
        stack_deets = f.read()
    except IOError as e:
      print("Could not open {0}/{1}_deets.txt for reading!".format(cache_dir, stack_name))
      print(e)
      exit()
    return stack_deets

  def parse_openstack_details(self):
    backend_nodes = []
    backend_re = re.compile('^BACKEND: (.*)')
    seed_re = re.compile('^BACKEND_SEEDS: (.*)')
    for line in self.stack_details.splitlines():
      match = backend_re.match(line)
      if match:
        print("Backend Line: {0}".format(match.group(1)))
        backend_nodes.append(match.group(1))
      match = seed_re.match(line)
      if match:
        print("Seed Line: {0}".format(match.group(1)))
        seeds = match.group(1).split(',')
    self.backend_nodes = []
    for backend in backend_nodes:
      (name, id, ip) = backend.split(':')
      if [x for x in seeds if ip == x]:
        self.backend_nodes.append("{0}:seed".format(backend))
      else:
        self.backend_nodes.append("{0}:not_seed".format(backend))
    self.seeds = seeds

  def remove_node(self, manifest, node):
    manifest.remove_node(self.manifest_name, node)

  def clear_manifest(self, manifest):
    if manifest.exists(self.manifest_name):
      node_list = manifest.get_nodes(self.manifest_name)
      for node_line in node_list:
        print(node_line)
        (node_name, node_id, node_ip, seed_state) = node_line.split(':')
        print("Clearing {0} from manifest...".format(node_name))
        self.remove_node(manifest, node_name)
      manifest.write_nodes(self.manifest_name, [])

  def create_manifest(self, manifest):
    if not manifest.exists(self.manifest_name):
      manifest.new_cluster(self.manifest_name)
    for node in self.backend_nodes:
      print("Adding {0} to manifest...".format(node))
      self.add_node(manifest, node)
    manifest.write_nodes(self.manifest_name, self.backend_nodes)

  def add_node(self, manifest, node):
    s = self.settings
    node_name = node.split(':')[0]
    seeds = ','.join(self.seeds)
    with open("{0}/../files/node-data.yaml.template".format(script_dir), 'r') as f:
      data_template=Template(f.read())
    with open("{0}/../files/node-manifest.pp.template".format(script_dir), 'r') as f:
      manifest_template=Template(f.read())
    data_text = data_template.substitute(cluster_name=s['cluster_name'], DC=s['DC'], rack=s['rack'], package_ensure=s['package_ensure'], package=s['package'])
    manifest_text = manifest_template.substitute(node=node_name, seeds=seeds)
    fact_text = "fc_playlister_be_test=success\nfc_playlister_be::test=success"
    manifest.add_node(self.manifest_name, node_name, data_text, manifest_text, fact_text)



class PuppetManifest ():
  def __init__(self, manifest_path, environment, puppetmaster):
    self.path = manifest_path
    self.environment = environment
    self.puppetMasterFiles = PuppetMasterFiles(puppetmaster)

  def pull(self):
    try:
      run_git = subprocess.run(["/usr/bin/git", "checkout", self.environment], cwd=self.path)
      if run_git.returncode:
        raise Exception("Could not check out branch {0} in {1}".format(self.environment, self.path))
      run_git = subprocess.run(["/usr/bin/git", "pull"], cwd=self.path)
      if run_git.returncode:
        raise Exception("Could not update {0}".format(self.path))
    except Exception as e:
      print("Failed to update puppet-manifests: {0}".format(e))
      exit()

  def new_cluster(self, cluster):
    if self.exists(cluster):
      raise Exception("Cannot create, cluster {0} already exists!".format(cluster))
    cluster_path = "{0}/{1}".format(self.path, cluster)
    os.mkdir(cluster_path)
    Path("{0}/node.list".format(cluster_path)).touch()
    
  def add_node(self, cluster, node, data, manifest, facts):
    cluster_path = "{0}/{1}".format(self.path, cluster)
    with open("{0}/data-{1}.yaml".format(cluster_path, node), 'w') as f:
      f.write(data)
    self.puppetMasterFiles.sync("{0}/data-{1}.yaml".format(cluster_path, node), "data/nodes/{0}.novalocal.yaml".format(node))
    with open("{0}/manifest-{1}.pp".format(cluster_path, node), 'w') as f:
      f.write(manifest)
    self.puppetMasterFiles.sync("{0}/manifest-{1}.pp".format(cluster_path, node), "manifests/{0}.novalocal.pp".format(node))
    with open("{0}/facter-{1}.txt".format(cluster_path, node), 'w') as f:
      f.write(facts)
    self.puppetMasterFiles.sync("{0}/facter-{1}.txt".format(cluster_path, node), "site-modules/fc_playlister_be/files/dynamic_facter/{0}.novalocal.txt".format(node))

  def get_nodes(self, cluster):
    cluster_path = "{0}/{1}".format(self.path, cluster)
    node_file = "{0}/{1}/node.list".format(self.path, cluster)
    try:
      with open(node_file, 'r') as f:
        node_lines=f.read().splitlines()
    except IOError as e:
      print("Could not read nodes from {0}!".format(node_file))
      print(e)
      exit()
    return node_lines

  def write_nodes(self, cluster, node_list):
    cluster_path = "{0}/{1}".format(self.path, cluster)
    node_file = "{0}/node.list".format(cluster_path)
    try:
      with open(node_file, 'w') as f:
        f.write('\n'.join(node_list))
    except IOError as e:
      print("Could not write nodes to {0}!".format(node_file))
      print(e)
      exit()

  def exists(self, cluster):
    manifest_path = "{0}/{1}".format(self.path, cluster)
    return os.path.isdir(manifest_path)

  def remove_node(self, cluster, node):
    cluster_path = "{0}/{1}".format(self.path, cluster)
    self.puppetMasterFiles.delete("data/nodes/{0}.novalocal.yaml".format(node))
    self.puppetMasterFiles.delete("manifests/{0}.novalocal.pp".format(node))
    self.puppetMasterFiles.delete("site-modules/fc_playlister_be/files/dynamic_facter/{0}.novalocal.txt".format(node))
    print("Removing manifest node {0}".format(node))


class PuppetMasterFiles ():
  def __init__(self, puppetmaster, code_dir='/etc/puppetlabs/code/environments/production'):
    self.puppetmaster = puppetmaster
    self.code_dir = code_dir

  def sync(self, source_file, dest_file):
    sync_result = subprocess.run(["/usr/bin/rsync", source_file, "root@{0}".format(self.puppetmaster) + ":{0}/{1}".format(self.code_dir, dest_file)])

  def delete(self, dest_file):
    delete_result = subprocess.run(["/usr/bin/ssh", "root@{0}".format(self.puppetmaster),  "rm {0}/{1}".format(self.code_dir, dest_file)])


    
playlister = PlaylisterCluster(stack_name, reinitialize=True)
manifest = PuppetManifest(manifest_dir, "production", puppetmaster)
manifest.pull()
playlister.clear_manifest(manifest)
playlister.create_manifest(manifest)

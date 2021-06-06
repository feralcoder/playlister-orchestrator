import os
import subprocess
from pathlib import Path
import json

class PuppetManifest ():
  def __init__(self, manifest_path, cluster_name, environment, puppetmaster):
    self.path = manifest_path
    self.cluster_name = cluster_name
    self.cluster_path = "{0}/{1}".format(manifest_path, cluster_name)
    self.environment = environment
    self.puppetmaster = puppetmaster

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


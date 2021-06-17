import os
import subprocess
import logging, sys
from pathlib import Path
import json
from .puppet_master_files import PuppetMasterFiles

class PuppetManifest ():
  def __init__(self, manifest_path, cluster_name, puppetmaster, environment='production'):
    self.path = manifest_path
    self.cluster_name = cluster_name
    self.cluster_path = "{0}/{1}".format(manifest_path, cluster_name)
    self.environment = environment
    self.puppetmaster = puppetmaster
    self.puppet_master_files = PuppetMasterFiles(puppetmaster, "/etc/puppetlabs/code/environments/{0}".format(environment))

  # FLUSH cluster configs when not enough state exists to create cluster and manifest objects
  def flush_cluster(manifest_path, cluster_name, puppetmaster, environment):
    puppet_master_files = PuppetMasterFiles(puppetmaster, "/etc/puppetlabs/code/environments/{0}".format(environment))
    data_files     = puppet_master_files.list_files("data/nodes/")
    manifest_files = puppet_master_files.list_files("manifests/")
    facter_files   = puppet_master_files.list_files("site-modules/fc_common/files/dynamic_facter/")
    cluster_data_files     = filter(lambda x: x.startswith("{0}-".format(cluster_name)), data_files)
    cluster_manifest_files = filter(lambda x: x.startswith("{0}-".format(cluster_name)), manifest_files)
    cluster_facter_files   = filter(lambda x: "_{0}-".format(cluster_name) in x, facter_files)
    for file in cluster_data_files:
      logging.info("Deleting data/nodes/{0} on puppetmaster...".format(file))
      puppet_master_files.delete("data/nodes/{0}".format(file))
    for file in cluster_manifest_files:
      logging.info("Deleting manifests/{0} on puppetmaster...".format(file))
      puppet_master_files.delete("manifests/{0}".format(file))
    for file in cluster_facter_files:
      logging.info("Deleting site-modules/fc_common/files/dynamic_facter/{0} on puppetmaster...".format(file))
      puppet_master_files.delete("site-modules/fc_common/files/dynamic_facter/{0}".format(file))

    cluster_path = "{0}/{1}".format(manifest_path, cluster_name)
    if os.path.isdir(cluster_path):
      for file in os.listdir(cluster_path):
        logging.info("Deleting {0}/{1}".format(cluster_path, file))
        os.remove("{0}/{1}".format(cluster_path, file))
      logging.info("Deleting {0}".format(cluster_path))
      os.rmdir(cluster_path)

  ### REFACTORING
  def deploy_node_configs(self, node):
    self.puppet_master_files.sync("{0}/data-{1}.yaml".format(self.cluster_path, node['name']), "data/nodes/{0}.novalocal.yaml".format(node['name']))
    self.puppet_master_files.sync("{0}/manifest-{1}.pp".format(self.cluster_path, node['name']), "manifests/{0}.novalocal.pp".format(node['name']))
    self.puppet_master_files.sync("{0}/facter-{1}.txt".format(self.cluster_path, node['name']), "site-modules/fc_common/files/dynamic_facter/{0}_{1}.novalocal.txt".format(node['type'], node['name']))

  def undeploy_node_configs(self, node):
    self.puppet_master_files.delete_if_present("data/nodes/{0}.novalocal.yaml".format(node['name']))
    self.puppet_master_files.delete_if_present("manifests/{0}.novalocal.pp".format(node['name']))
    self.puppet_master_files.delete_if_present("site-modules/fc_playlister_be/files/dynamic_facter/{0}.novalocal.txt".format(node['name']))

  # push: also remove puppetmaster configs
  def remove_node(self, node_name, push=False):
    logging.info("Removing manifest node {0}".format(node_name))
    for file in ["{0}/data-{1}.yaml".format(self.cluster_path, node_name), "{0}/manifest-{1}.pp".format(self.cluster_path, node_name), "{0}/facter-{1}.txt".format(self.cluster_path, node_name)]:
      if os.path.isfile(file): os.remove(file)
    nodes = self.get_node_list()
    for node in nodes:
      if node['name'] == node_name:
        nodes.remove(node)
        if push:
          self.undeploy_node_configs(node)
          logging.info("Removing  node {0} from puppetmaster".format(node_name))
    self.write_node_list(nodes)

  def write_node_list(self, node_list):
    node_file = "{0}/node.list".format(self.cluster_path)
    try:
      with open(node_file, 'w') as f:
        for node in node_list:
          json.dump(node, f)
          f.write('\n')
    except IOError as e:
      logging.error("Could not write nodes to {0}!".format(node_file))
      logging.error(e)
      exit()



  ### ORIG, REFACTOR
  def git_pull(self):
    try:
      run_git = subprocess.run(["/usr/bin/git", "checkout", self.environment], cwd=self.path)
      if not run_git:
        raise Exception("Could not check out branch {0} in {1}".format(self.environment, self.path))
      run_git = subprocess.run(["/usr/bin/git", "pull"], cwd=self.path)
      if not run_git:
        raise Exception("Could not update {0}".format(self.path))
    except Exception as e:
      logging.error("Failed to update puppet-manifests: {0}".format(e))
      exit()

  def new_cluster(self):
    if self.cluster_exists():
      raise Exception("Cannot create, cluster {0} already exists!".format(self.cluster_name))
    os.mkdir(self.cluster_path)
    Path("{0}/node.list".format(self.cluster_path)).touch()

  # REQUIRES CALLER TO MANAGE ADDING NODE TO NODE LIST!
  def configure_node(self, node, node_configs, push=False):
    node_name = node['name']
    with open("{0}/data-{1}.yaml".format(self.cluster_path, node_name), 'w') as f:
      f.write(node_configs['data'])
    with open("{0}/manifest-{1}.pp".format(self.cluster_path, node_name), 'w') as f:
      f.write(node_configs['manifest'])
    with open("{0}/facter-{1}.txt".format(self.cluster_path, node_name), 'w') as f:
      f.write(node_configs['facts'])
    if push:
      self.deploy_node_configs(node)

  def get_node_list(self):
    node_file = "{0}/node.list".format(self.cluster_path)
    try:
      with open(node_file, 'r') as f:
        node_lines=f.read().splitlines()
    except IOError as e:
      logging.error("Could not read nodes from {0}!".format(node_file))
      logging.error(e)
      exit()
    nodes = []
    for line in node_lines:
      nodes.append(json.loads(line))
    return nodes

  def cluster_exists(self):
    return os.path.isdir(self.cluster_path)


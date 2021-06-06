import os
import sys
from orchestrator import HostCommander, NodeManager, PlaylisterDeployer, PuppetManifest

stack_name = sys.argv[1]
script_dir=os.path.dirname(os.path.realpath(__file__))
manifest_dir="{0}/puppet-manifests".format(script_dir)
puppetmaster = 'puppetmaster.feralcoder.org'


if __name__ == "__main__":
  manifest = PuppetManifest(manifest_dir, stack_name, "production", puppetmaster)
  manifest.git_pull()
  playlister_deployer = PlaylisterDeployer(stack_name, manifest, script_dir)

  # NEW MARIADB WAY
  #playlister_deployer.deploy_this_thing()
  #playlister_deployer.start_galera()
  #playlister_deployer.load_schema()
  #playlister_deployer.start_columnnstore()
  #playlister_deployer.shutdown_galera()
  #playlister_deployer.shutdown_columnstore()

  # OLD CASSANDRA WAY
  #playlister_deployer.deploy_this_thing()
  #playlister_deployer.start_cassandra()
  #playlister_deployer.load_schema()
  #playlister_deployer.nominalize()
  #playlister_deployer.shutdown_cassandra()

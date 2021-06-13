import os
import sys
from orchestrator import HostCommander, NodeManager, PlaylisterDeployer, PuppetManifest
import logging, sys

stack_name = sys.argv[1]
script_dir=os.path.dirname(os.path.realpath(__file__))
manifest_dir="{0}/puppet-manifests".format(script_dir)
puppetmaster = 'puppetmaster.feralcoder.org'

log_level=logging.INFO
logging.basicConfig(stream=sys.stderr, level=log_level)

if __name__ == "__main__":
  manifest = PuppetManifest(manifest_dir, stack_name, puppetmaster, "production")
  logging.debug(repr(manifest))
  manifest.git_pull()
  playlister_deployer = PlaylisterDeployer(stack_name, manifest, script_dir)
  logging.debug(repr(playlister_deployer))

  # DEPLOY PLAYLISTER
  # create_cluster done for OLAP / OLTP services...
  playlister_deployer.create_cluster()
  # IMPLEMENT:
  #playlister_deployer.load_schema()

  # START PLAYLISTER
  #playlister_deployer.start_transaction_db()
  # IMPLEMENT:
  #playlister_deployer.start_analytics_db()

  # STOP PLAYLISTER
  #playlister_deployer.stop_transaction_db()
  # IMPLEMENT:
  #playlister_deployer.stop_analytics_db()

  # DEPLOY PLAYLISTER
  playlister_deployer.deploy_playlister_code(parallel=True)




  # OLD CASSANDRA WAY
  #playlister_deployer.deploy_this_thing()
  #playlister_deployer.start_cassandra()
  #playlister_deployer.load_schema()
  #playlister_deployer.nominalize()
  #playlister_deployer.shutdown_cassandra()

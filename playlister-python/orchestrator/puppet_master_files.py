import subprocess

class PuppetMasterFiles ():
  def __init__(self, puppetmaster, code_dir='/etc/puppetlabs/code/environments/production'):
    self.puppetmaster = puppetmaster
    self.code_dir = code_dir

  def sync(self, source_file, dest_file):
    sync_result = subprocess.run(["/usr/bin/rsync", source_file, "root@{0}".format(self.puppetmaster) + ":{0}/{1}".format(self.code_dir, dest_file)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  def delete(self, dest_file):
    delete_result = subprocess.run(["/usr/bin/ssh", "root@{0}".format(self.puppetmaster),  "rm {0}/{1}".format(self.code_dir, dest_file)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

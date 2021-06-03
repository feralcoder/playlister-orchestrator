import subprocess

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



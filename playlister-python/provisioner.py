from openstack_auth import OsOpenRC, KeystoneClient, KeystoneSession, \
    CinderClient, NovaCredentials, NovaClient, GlanceClient, NeutronClient
from manifest import sec_groups as sec_group_manifest, servers as server_manifest, load_balancers as lb_manifest, \
    lb_listeners as listener_manifest, lb_pools as pool_manifest
import novaclient


openrc = OsOpenRC()
session = KeystoneSession(openrc).session
keystoneClient = KeystoneClient(session).client
glanceClient = GlanceClient(session).client
cinderClient = CinderClient(session).client

novaCredentials = NovaCredentials(openrc)
novaClient = NovaClient(novaCredentials.getCredentials()).client
neutronClient = NeutronClient(session).client


projects = keystoneClient.projects.list()
volumes = cinderClient.volumes.list()
servers = novaClient.servers.list()


def get_image_by_name(name):
    image_list = glanceClient.images.list()
    for image in image_list:
        if image['name'] == name:
            return image['id']


def get_network_by_name(name):
    netw = neutronClient.list_networks()
    network_list = netw['networks']
    for network in network_list:
        if network['name'] == name:
            return network['id']


for server_type in server_manifest.keys():
    print("Server Type: {0}".format(server_type))
    flavor = novaClient.flavors.find(name=server_manifest[server_type]['flavor'])
    network = get_network_by_name(server_manifest[server_type]['network'])
    image = get_image_by_name(server_manifest[server_type]['image'])
    count = server_manifest[server_type]['count']
    key_name = server_manifest[server_type]['key-name']
    security_group = server_manifest[server_type]['security-group']
    for i in range(1, count):
        test=novaClient.servers.create(name="{0}___{1}".format(server_type, i), image=image, flavor=flavor, key_name=key_name, \
                                  security_group=security_group, nics=[{'net-id': network}], meta={'mytag': server_type})

for security_group in sec_group_manifest.keys():
    print("Security Group: {0}".format(security_group))
for load_balancer in lb_manifest.keys():
    print("Load Balancer: {0}".format(load_balancer))
for lb_listener in listener_manifest.keys():
    print("LB Listener: {0}".format(lb_listener))
for lb_pool in pool_manifest.keys():
    print("LB Pool: {0}".format(lb_pool))

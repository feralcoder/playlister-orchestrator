sec_groups = {}
sec_groups['playlister_frontend'] = [ {'direction': 'ingress', 'protocol': 'tcp', 'dst-port': '22'},
                                      {'direction': 'ingress', 'protocol': 'tcp', 'dst-port': '80'},
                                      {'direction': 'ingress', 'protocol': 'tcp', 'dst-port': '443'},
                                      {'direction': 'ingress', 'protocol': 'icmp'},
                                      {'direction': 'egress', 'protocol': 'tcp', 'dst-port': '1:65535'},
                                      {'direction': 'egress', 'protocol': 'udp', 'dst-port': '1:65535'},
                                      {'direction': 'egress', 'protocol': 'icmp'} ]
sec_groups['playlister_listdb'] = [ {'direction': 'ingress', 'protocol': 'tcp', 'dst-port': '22'},
                                      {'direction': 'ingress', 'protocol': 'tcp', 'dst-port': '7000:7001'},
                                      {'direction': 'ingress', 'protocol': 'tcp', 'dst-port': '7199'},
                                      {'direction': 'ingress', 'protocol': 'tcp', 'dst-port': '9042'},
                                      {'direction': 'ingress', 'protocol': 'tcp', 'dst-port': '9142'},
                                      {'direction': 'ingress', 'protocol': 'tcp', 'dst-port': '9160'},
                                      {'direction': 'ingress', 'protocol': 'icmp'},
                                      {'direction': 'egress', 'protocol': 'tcp', 'dst-port': '1:65535'},
                                      {'direction': 'egress', 'protocol': 'udp', 'dst-port': '1:65535'},
                                      {'direction': 'egress', 'protocol': 'icmp'} ]


servers = {}
servers['playlister_frontend'] = {'count': 3, 'flavor': 'm1.medium', 'image': 'ubuntu-20.4', 'key-name': 'cliff_admin', 'network': 'admin1-net', 'security-group': 'playlister_frontend'}
servers['playlister_listdb'] = {'count': 4, 'flavor': 'm1.medium', 'image': 'ubuntu-20.4', 'key-name': 'cliff_admin', 'network': 'admin1-net', 'security-group': 'playlister_listdb'}

load_balancers = {}
load_balancers['playlister_frontend'] = { 'vip-network-id': 'public1', 'vip-address': '172.30.1.20' }

# Many-to-one to load_balancers
lb_listeners = {}
lb_listeners['playlister_frontend_http'] = { 'load_balancer': 'playlister_frontend', 'protocol': 'TCP', 'protocol-port': 22 }
lb_listeners['playlister_frontend_https'] = { 'load_balancer': 'playlister_frontend', 'protocol': 'TCP', 'protocol-port': 443 }

# Automatically associate with same-named listeners
# TEST: try same pool for multiple listeners
lb_pools = {}
lb_pools['playlister_frontend_http'] = { 'member_tag': 'playlister_frontend', 'lb-algorithm': 'ROUND_ROBIN', 'protocol': 'TCP'}
lb_pools['playlister_frontend_https'] = { 'member_tag': 'playlister_frontend', 'lb-algorithm': 'ROUND_ROBIN', 'protocol': 'TCP'}

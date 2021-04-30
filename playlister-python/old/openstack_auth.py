import os
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient import client as keystoneClient
from glanceclient import client as glanceClient
from cinderclient import client as cinderClient
from novaclient.client import Client as novaClient
from neutronclient.v2_0 import client as neutronClient


class OsOpenRC:
    def __init__(self):
        self.projectDomainName = os.getenv('OS_PROJECT_DOMAIN_NAME')
        self.userDomainName = os.getenv('OS_USER_DOMAIN_NAME')
        self.projectName = os.getenv('OS_PROJECT_NAME')
        self.tenantName = os.getenv('OS_TENANT_NAME')
        self.userName = os.getenv('OS_USERNAME')
        self.password = os.getenv('OS_PASSWORD')
        self.authURL = os.getenv('OS_AUTH_URL')
        self.interface = os.getenv('OS_INTERFACE')
        self.endpointType = os.getenv('OS_ENDPOINT_TYPE')
        self.identityAPIVersion = os.getenv('OS_IDENTITY_API_VERSION')
        self.regionName = os.getenv('OS_REGION_NAME')
        self.authPlugin = os.getenv('OS_AUTH_PLUGIN')


class KeystoneSession:
    def __init__(self, openrc):
        self.auth = v3.Password(auth_url=openrc.authURL,
                                username=openrc.userName,
                                password=openrc.password,
                                user_domain_name=openrc.userDomainName,
                                project_domain_name=openrc.projectDomainName,
                                project_name=openrc.projectName)
        self.session = session.Session(auth=self.auth)


class KeystoneClient:
    def __init__(self, session):
        self.client = keystoneClient.Client(session=session)


class GlanceClient:
    def __init__(self, session):
        self.client = glanceClient.Client(2, session=session)


class CinderClient:
    def __init__(self, session):
        self.client = cinderClient.Client(3, session=session)


class NovaCredentials:
    def __init__(self, openrc):
        self.cred = {}
        self.cred['version'] = '2'
        self.cred['username'] = openrc.userName
        self.cred['password'] = openrc.password
        self.cred['auth_url'] = openrc.authURL
        self.cred['user_domain_name'] = openrc.userDomainName
        self.cred['project_domain_name'] = openrc.projectDomainName
        self.cred['tenant_name'] = openrc.tenantName
        self.cred['project_name'] = openrc.projectName

    def getCredentials(self):
        creds = self.cred.copy()
        creds['version'] = '2'
        return creds


class NovaClient:
    def __init__(self, credentials):
        self.client = novaClient(**credentials)


class NeutronClient:
    def __init__(self, session):
        self.client = neutronClient.Client(session=session)
#        self.client = neutronClient(**credentials)

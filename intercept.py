#!/usr/bin/python
# Author Markku Rantanen, markku@arista.com
# 
from jsonrpclib import Server
import optparse
import socket, struct

vlan = '0'
number = '0'

# Following functions will use networking socket to turn IP address to numbers and make sure that subnetting rolls over nicely when autocreating IP addresses for SVIs

def ip2long(ip):
    """
    Convert an IP string to long
    """
    packedIP = socket.inet_aton(ip)
    return struct.unpack("!L", packedIP)[0]
    
def long2ip(long):
    """
    Convert a long to an IP string
    """
    stringIP = socket.inet_ntoa(struct.pack('!L', long))
    return stringIP

# Options for the commands to use this script
usage = 'usage: %prog [options]'
op = optparse.OptionParser(usage=usage)
op.add_option( '-c', '--intercept', dest='intercept', action='store', help='IP Address for Intercept VTEP leaf switch', type='string')
op.add_option( '-i', '--int', dest='interface', action='store', help='Interface for connecting the host', type='string')
op.add_option( '-v', '--vlan', dest='vlan', action='store', help='Base VLAN id', type='string')
op.add_option( '-n', '--number', dest='number', action='store', help='Number of VLANs', type='string')
op.add_option( '-a', '--address', dest='address', action='store', help='Base IP address for the VLAN interfaces', type='string')
op.add_option( '-r', '--recirc', dest='recirc', action='store', help='Enable Re-Circulation for VXLAN routing', type='string')
op.add_option( '-x', '--vxlan', dest='vxlan', action='store', help='Enable VXLAN interface', type='string')
op.add_option( '-l', '--lbk', dest='loopback', action='store', help='Enable Loopback 1 interface, give IP address for the loopback interface', type='string')
op.add_option( '-d', '--dflow', dest='dflow', action='store', help='Enable DirectFlow on the Leaf switch', type='string')
op.add_option( '-o', '--cvx', dest='cvx', action='store', help='Enable CVX connection', type='string')
op.add_option( '-u', '--userid', dest='userid', action='store', help='Username', type='string')
op.add_option( '-p', '--passwd', dest='passwd', action='store', help='Password', type='string')
op.add_option( '-m', '--vMac', dest='vMac', action='store', help='Virtual Mac Address for VARP settings', type='string')

opts, _ = op.parse_args()

# extract parameters
device = opts.intercept
interface = opts.interface
vlan = opts.vlan
number = opts.number
address = opts.address
recirc = opts.recirc
vXlan = opts.vxlan
directflow = opts.dflow
cvx = opts.cvx
userName = opts.userid
passWord = opts.passwd
loopBack = opts.loopback
vMac = opts.vMac


# use list of commands to identify if any command is left empty
#cmdList = deviceSet, fw, tag, vni, policy, state, vXlan
creDentials = userName, passWord
loopBackIp = str(loopBack)+"/32"

baseVNI = 10
maxVlan = int(vlan)+int(number)-1 # create a range of VLANs starting from the base VLAN
rangeVlan = vlan+"-"+str(maxVlan)

# Create proxy setting for the switch with credentials
switch = Server( 'http://%s:%s@%s/command-api' % ( userName, passWord, device ) )

# create re-circulation configuration for VXLAN routing 
if recirc != None:
	response = switch.runCmds(1, ["enable", "configure", "service interface unconnected expose", "interface UnconnectedEthernet 1", "traffic-loopback source device mac", "channel-group recirculation 1", "interface Recirc-Channel 1", "no swithcport", "switchport recirculation features vxlan"])
# Create virtual mac address for VARP setting
if vMac != None:
	response = switch.runCmds(1, ["enable", "configure", "ip virtual-router mac-address %s" % (vMac)])

# if you enable directflow it will turn it on in CLI
if directflow != None:
	response = switch.runCmds(1, ["enable", "configure", "directflow", "no shutdown"])

# check if CVX was requested to be enabled
if cvx != None:
	response = switch.runCmds(1, ["enable", "configure", "management cvx", "no shutdown", "server host %s" % (cvx)]) 

# Create VXLAN interface
if vXlan != None:
	response = switch.runCmds(1, ["enable", "configure", "interface vxlan 1", "no shutdown", "vxlan controller-client", "vxlan source-interface loopback 1"])
	response = switch.runCmds(1, ["enable", "configure", "interface loopback 1", "ip address %s" % (loopBackIp)])

count = 0
# the above is used only if vxlan interface does not exist
# the below is regardless of that to create static vlan to vni mappings
while count < int(number):
        vlanId = int(vlan)+count
        vni = str(baseVNI)+str(vlanId)
        vxlanCmd1 = "vxlan vlan %s" % (vlanId)
        vxlanCmd2 = "vni %s" % (vni)
        vxlanCmd3 = vxlanCmd1+" "+vxlanCmd2
	response = switch.runCmds(1, ["enable", "configure", "interface vxlan 1", vxlanCmd3])
        count +=1	
# create VLANS
#
count = 0
while count < int(number):
	vlans = int(vlan)+count
	response = switch.runCmds(1, ["enable", "configure", "vlan %s" % (str(vlans)) ])
	count +=1

# Create inteface for the host
if int(number) == 1: # avoid using vlan-range like 100-100, to limit single vlan to just one value
        rangeVlan = vlan
response = switch.runCmds(1, ["enable", "configure", "interface %s" % (interface), "no shutdown", "switchport mode trunk", "switchport trunk allowed vlan %s" % (rangeVlan)])

# create VLAN interfaces and their IP addresses
count = 0
if address != None:
	while count < int(number):
  		ipnum = ip2long(address) + count*256;
  		ip = long2ip(ipnum);
  		vlanInt = int(vlan) + count
  		varpIP = ip+"/24"
		vlanCmd = "interface vlan %s" % (str(vlanInt))
		ipAddress = "ip address virtual %s" % (varpIP)
		response = switch.runCmds(1, ["enable", "configure", vlanCmd, ipAddress])
		count +=1

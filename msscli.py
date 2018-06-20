#!/usr/bin/python
# Author Markku Rantanen, markku@arista.com
#
from jsonrpclib import Server
import optparse

# Following are the commands to check MSS status on CVX
cmnd = 'show service mss status'
cmnd2 = 'show service mss zone'
cmnd3 = 'show service vxlan status'


# Options for the commands to use this script
usage = 'usage: %prog [options]'
op = optparse.OptionParser(usage=usage)
op.add_option( '-c', '--cvx', dest='cvx', action='store', help='IP Address for CVX', type='string')
op.add_option( '-d', '--dev', dest='dev', action='store', help='Name of the Palo Alto Device Set', type='string')
op.add_option( '-f', '--fw', dest='fw', action='store', help='Name of the Firewall', type='string')
op.add_option( '-t', '--tag', dest='tag', action='store', help='Name of the Palo Alto TAG', type='string')
op.add_option( '-v', '--vni', dest='vni', action='store', help='VNI range for Service VNIs', type='string')
op.add_option( '-o', '--policy', dest='policy', action='store', help='Policy Management, options Firewall or Panorama', type='string')
op.add_option( '-s', '--state', dest='state', action='store', help='State, options, active, shutdown or suspend', type='string')
op.add_option( '-x', '--vxlan', dest='vxlan', action='store', help='Enable VXLAN service under CVX', type='string')
op.add_option( '-u', '--userid', dest='userid', action='store', help='Userid', type='string')
op.add_option( '-p', '--password', dest='passwd', action='store', help='Password', type='string')
op.add_option( '-y', '--status', dest='status', action='store', help='Check MSS and VXLAN services status on selected CVX', type='string')

opts, _ = op.parse_args()

# extract parameters
cvx = opts.cvx
deviceSet = opts.dev
fw = opts.fw
tag = opts.tag
vni = opts.vni
policy = opts.policy
state = opts.state
vXlan = opts.vxlan
userName = opts.userid
passWord = opts.passwd
statuS = opts.status

# use list of commands to identify if any command is left empty
cmdList = deviceSet, fw, tag, vni, policy, state, vXlan
creDentials = userName, passWord
if statuS == None:
	for cmnds in cmdList:
		if  cmnds == None:
		   print cmdList
		   print "Must give all parameters, except status. Status will show CVX status. Use -h or --help option for details"
		   exit()

# Create proxy setting for the switch with credentials
switch = Server( 'http://%s:%s@%s/command-api' % ( userName, passWord, cvx ) )


# If status is requested then run these for MSS status commands
if statuS != None:
 	for items in creDentials:
		if items == None:
			print "Must give username and password for getting CVX status information"
			exit()	
	response = switch.runCmds( 1, ["enable", cmnd] )
	isEnabled = response[1]['enabled']
	serviceVNI = response[1]['serviceVni']
	print cmnd
	print "======================="
	print "MSS enabled : ",isEnabled
	print "Service VNIs: ", serviceVNI
	print "!"
	response = switch.runCmds( 1, ["enable", cmnd2] )
	mssSource = response[1]['sources']
	print cmnd2
	print "Source: ",mssSource
	print "!"
	response = switch.runCmds( 1, ["enable", cmnd3] )
	cvxStatus = response[1]['status']
	print cmnd3
	print "Status : ", cvxStatus
	print "!"

# if status is not requested then run the commands for enabling MSS on CVX.
elif statuS == None:
	for items in creDentials:
                if items == None:
                        print "Must give username and password for getting CVX status information"
                        exit()
	response = switch.runCmds(1, ["enable", "configure", "cvx", "no shutdown", "service vxlan", "no shutdown", "service mss", "no shutdown", "vni range %s" % (vni), "dynamic device-set %s" % (deviceSet), "tag %s" % (tag), "type palo-alto %s" % (policy), "state %s" % (state), "device %s" % (fw)] ) 

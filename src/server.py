import re
# 第三方库
from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp, udp6
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from pysnmp.proto.rfc1905 import VarBind
# 自己的库
from settings import log, SNMP_PORT
 

def pick(varbind):
    pattern="name=(.*)[\s\S]*value=(.*)"
    regx = re.compile(pattern)
    matchs = regx.findall(varbind)
    if matchs:
        return matchs[0][0],matchs[0][1]
    else:
        return False
 

def cbFun(transportDispatcher, transportDomain, transportAddress, wholeMsg):
    while wholeMsg:
        msgVer = int(api.decodeMessageVersion(wholeMsg))
        if msgVer in api.protoModules:
            pMod = api.protoModules[msgVer]
        else:
            log.info('Unsupported SNMP version %s' % msgVer)
            return
        reqMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=pMod.Message(),)
        # log.info("reqmsg:", reqMsg)
        # log.info("wholemsg:",wholeMsg)
        log.info('Notification message from %s:%s: ' % (transportDomain, transportAddress))
        reqPDU = pMod.apiMessage.getPDU(reqMsg)
        # log.info("pdu:",reqPDU)
        varBinds = pMod.apiPDU.getVarBindList(reqPDU)
        # log.info("varbinds:",varBinds)
        for row in varBinds:
            row: VarBind
            row = row.prettyPrint()
            k, v = pick(row)
            log.info("%s:%s" % (k,v))
    return wholeMsg
 

def main():
    listen_ip = '0.0.0.0'
    listen_port = SNMP_PORT
    transportDispatcher = AsynsockDispatcher()
    transportDispatcher.registerRecvCbFun(cbFun)
    # UDP/IPv4
    transportDispatcher.registerTransport(
        udp.domainName, udp.UdpSocketTransport().openServerMode((listen_ip, listen_port))
    )
    # UDP/IPv6
    #  transportDispatcher.registerTransport(
        #  udp6.domainName, udp6.Udp6SocketTransport().openServerMode(('::1', listen_port))
    #  )
    log.info(f'listening on {listen_ip}:{listen_port}')
    transportDispatcher.jobStarted(1)
    try:
        transportDispatcher.runDispatcher()
    except:
        transportDispatcher.closeDispatcher()
        raise
 

if __name__ == '__main__':
    main()


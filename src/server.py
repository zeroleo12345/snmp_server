import re
import traceback
# 第三方库
from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp, udp6
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from pysnmp.proto.rfc1905 import VarBind
from pysnmp.smi import builder, view, compiler
# 自己的库
from settings import log, SNMP_PORT
from utils.feishu import Feishu


mibBuilder = builder.MibBuilder()
mibBuilder.addMibSources(builder.DirMibSource('/root/.pysnmp/mibs/'))
mibBuilder.loadModules('HH3C-NQA-MIB')
mibView = view.MibViewController(mibBuilder)
 

def pick(varbind):
    pattern="name=(.*)[\s\S]*value=(.*)"
    regx = re.compile(pattern)
    matchs = regx.findall(varbind)
    if matchs:
        return matchs[0][0],matchs[0][1]
    else:
        return False
 

def callback(transportDispatcher, transportDomain, ip_and_port, wholeMsg):
    ip, port = ip_and_port
    while wholeMsg:
        try:
            msgVer = int(api.decodeMessageVersion(wholeMsg))
            if msgVer in api.protoModules:
                pMod = api.protoModules[msgVer]
            else:
                log.info(f'Unsupported SNMP version {msgVer}')
                return
            reqMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=pMod.Message(),)
        except Exception:
            log.trace(traceback.format_exc())
            return
        log.info(f'Notification message from {transportDomain}, ip: {ip}, port: {port}')
        reqPDU = pMod.apiMessage.getPDU(reqMsg)
        varBinds = pMod.apiPDU.getVarBindList(reqPDU)
        for row in varBinds:
            row: VarBind
            row = row.prettyPrint()
            oid_str, value = pick(row)
            #  log.info(f"{oid_str}: {value}")
            oid_int, label, suffix = mibView.getNodeName(tuple(int(s) for s in oid_str.split('.')))
            last_label = label[-1]
            log.info(f'[ {last_label} : {value} ]')
            # hh3cNqaReactCurrentStatus : 1-inactive关闭; 2-告警中; 3-active开启;
            if  last_label == 'hh3cNqaReactCurrentStatus' and str(value) == '2':
                msg = f'network lag > 300ms. ip: {ip}'
                log.warning(msg)
                Feishu.send_groud_msg(receiver_id=Feishu.FEISHU_SESSION_CHAT_ID, text=msg)
    return wholeMsg
 

def main():
    listen_ip = '0.0.0.0'
    listen_port = SNMP_PORT
    transportDispatcher = AsynsockDispatcher()
    transportDispatcher.registerRecvCbFun(callback)
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


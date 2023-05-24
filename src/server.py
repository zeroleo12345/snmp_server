import re
import traceback
# 第三方库
from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp
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
 

def pick(var_bind):
    pattern = "name=(.*)[\s\S]*value=(.*)"
    regex = re.compile(pattern)
    matchs = regex.findall(var_bind)
    if matchs:
        return matchs[0][0], matchs[0][1]
    else:
        return False
 

# https://pysnmp.readthedocs.io/en/latest/examples/v1arch/asyncore/manager/cmdgen/transport-tweaks.html
def callback(dispatcher, transport_domain, ip_and_port, whole_msg):
    ip, port = ip_and_port
    while whole_msg:
        try:
            msg_version = int(api.decodeMessageVersion(whole_msg))
            if msg_version in api.protoModules:
                proto = api.protoModules[msg_version]
            else:
                log.info(f'Unsupported SNMP version {msg_version}')
                return
            req_msg, whole_msg = decoder.decode(whole_msg, asn1Spec=proto.Message())
        except Exception as e:
            log.trace(traceback.format_exc())
            return
        community = proto.apiMessage.getCommunity(req_msg).asOctets().decode()
        log.info(f'Notification message from {transport_domain}, ip: {ip}, port: {port}, community: {community}')
        pdu = proto.apiMessage.getPDU(req_msg)
        variable_binds = proto.apiPDU.getVarBindList(pdu)
        pkt = {}
        for row in variable_binds:
            row: VarBind = row.prettyPrint()
            oid_str, value = pick(row)
            #  log.info(f"{oid_str}: {value}")
            oid_int, label, suffix = mibView.getNodeName(tuple(int(s) for s in oid_str.split('.')))
            last_label = label[-1]
            pkt[last_label] = value
        log.info(f'packet: {pkt}')
        # hh3cNqaReactCurrentStatus : 1-inactive关闭; 2-告警中; 3-active开启;
        if pkt.get('hh3cNqaReactCurrentStatus', None) == '2':
            msg = f"{pkt['pingCtlDescr']}. ip: {ip}, community: {community}"
            log.warning(msg)
            Feishu.send_groud_msg(receiver_id=Feishu.FEISHU_SESSION_CHAT_ID, text=msg)
    return whole_msg
 

def main():
    listen_ip = '0.0.0.0'
    listen_port = SNMP_PORT
    dispatcher = AsynsockDispatcher()
    dispatcher.registerRecvCbFun(callback)

    # UDP/IPv4
    dispatcher.registerTransport(
        udp.domainName, udp.UdpSocketTransport().openServerMode((listen_ip, listen_port))
    )
    log.info(f'listening on {listen_ip}:{listen_port}')

    # We might never receive any response as we sent request with fake source IP
    dispatcher.jobStarted(1)

    # Dispatcher will finish as all jobs counter reaches zero
    try:
        dispatcher.runDispatcher()
    finally:
        dispatcher.closeDispatcher()
 

if __name__ == '__main__':
    main()


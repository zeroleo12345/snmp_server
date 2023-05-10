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
 

def callback(transport_dispatcher, transport_domain, ip_and_port, whole_msg):
    ip, port = ip_and_port
    while whole_msg:
        try:
            msg_version = int(api.decodeMessageVersion(whole_msg))
            if msg_version in api.protoModules:
                proto_module = api.protoModules[msg_version]
            else:
                log.info(f'Unsupported SNMP version {msg_version}')
                return
            req_msg, whole_msg = decoder.decode(whole_msg, asn1Spec=proto_module.Message(),)
        except Exception as e:
            log.trace(traceback.format_exc())
            return
        log.info(f'Notification message from {transport_domain}, ip: {ip}, port: {port}')
        reqPDU = proto_module.apiMessage.getPDU(req_msg)
        variable_binds = proto_module.apiPDU.getVarBindList(reqPDU)
        for row in variable_binds:
            row: VarBind = row.prettyPrint()
            oid_str, value = pick(row)
            #  log.info(f"{oid_str}: {value}")
            oid_int, label, suffix = mibView.getNodeName(tuple(int(s) for s in oid_str.split('.')))
            last_label = label[-1]
            log.info(f'[ {last_label} : {value} ]')
            # hh3cNqaReactCurrentStatus : 1-inactive关闭; 2-告警中; 3-active开启;
            if last_label == 'hh3cNqaReactCurrentStatus' and str(value) == '2':
                msg = f'network lag > 300ms. ip: {ip}'
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
    # UDP/IPv6
    #  dispatcher.registerTransport(
        #  udp6.domainName, udp6.Udp6SocketTransport().openServerMode(('::1', listen_port))
    #  )
    log.info(f'listening on {listen_ip}:{listen_port}')
    dispatcher.jobStarted(1)
    try:
        dispatcher.runDispatcher()
    except Exception as e:
        dispatcher.closeDispatcher()
        raise
 

if __name__ == '__main__':
    main()


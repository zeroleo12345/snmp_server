"""
ac配置参考:
    https://www.sohu.com/a/496535833_99906077
    https://juejin.cn/post/6988416254646157320

    H3C MSR3600 MIB库下载链接: https://zhiliao.h3c.com/questions/dispcont/232042
    IF-MIB: https://www.h3c.com/cn/Service/Document_Software/Document_Center/Routers/Catalog/MSR/MSR_3600/
"""

import json
import traceback
# 第三方库
from pysnmp.hlapi import SnmpEngine, CommunityData, UsmUserData, usmHMACMD5AuthProtocol, \
    UdpTransportTarget, Udp6TransportTarget, \
    usmAesCfb128Protocol, ContextData, ObjectIdentity, ObjectType, \
    getCmd, nextCmd
# 项目库
from utils.redispool import get_redis
from settings import log, COMMUNITY_NAME


class Mib(object):
    oid_map = {
        'system': {'node_oid': '1.3.6.1.2.1.1', 'dictionary': {}},
        'sysName': {'node_oid': '1.3.6.1.2.1.1.5', 'child_oid': '0', 'dictionary': {}},
        'ifDescr': {'node_oid': '1.3.6.1.2.1.2.2.1.2', 'dictionary': {}}, # interface名称
        'ifOperStatus': {'node_oid': '1.3.6.1.2.1.2.2.1.8', 'child_oid': '1', 'dictionary': {'1': 'up', '2': 'down'}}, # interace状态
        'ifHighSpeed': {'node_oid': '1.3.6.1.2.1.31.1.1.1.15', 'dictionary': {}}, # 百兆-100, 千兆-1000
        'ifInOctets': {'node_oid': '1.3.6.1.2.1.2.2.1.10', 'dictionary': {}}, #
        'ifHCInOctets': {'node_oid': '1.3.6.1.2.1.31.1.1.1.6', 'dictionary': {}}, # 取端口入方向字节数
        'ifHCOutOctets': {'node_oid': '1.3.6.1.2.1.31.1.1.1.10', 'dictionary': {}}, # 取端口出方向字节数
        'hh3cEntityExtCpuUsage': {'node_oid': '1.3.6.1.4.1.25506.2.6.1.1.1.1.6', 'child_oid': '11', 'dictionary': {}}, # 单板CPU利用率
        'hh3cEntityExtMemUsage': {'node_oid': '1.3.6.1.4.1.25506.2.6.1.1.1.1.8', 'child_oid': '1', 'dictionary': {}}, # 单板内存利用率
    }

    def __init__(self, ip, port=161):
        log.info(f'')
        log.info(f'')
        log.info(f'############################################')
        # 初始化引擎
        self.engine = SnmpEngine()
        # 选择 SNMP 协议，v1 和 v2c 只用团体字，使用 CommunityData 类实例化

        # SNMPv1
        # communityData = CommunityData('public', mpModel=0)

        # SNMPv2c
        self.communityData = CommunityData(COMMUNITY_NAME, mpModel=1)

        # SNMPv3, 则需要用户凭证, 使用 UsmUserData 类实例化, 认证和加密算法与上面设备配置相对应
        self.userData = UsmUserData(
            userName='admin',
            authKey='Admin@h3c',
            privKey='Admin@h3c',
            authProtocol=usmHMACMD5AuthProtocol,
            privProtocol=usmAesCfb128Protocol,
        )

        # 配置目标主机
        # ip_port = ('10.13.0.11', 161)
        timeout = 1.0
        retries = 0
        ip_port = (ip, port)
        if ":" in ip:
            log.info(f'IPv6: {ip}')
            self.target = Udp6TransportTarget(ip_port, timeout=timeout, retries=retries)
        else:
            log.info(f'IPv4: {ip}')
            self.target = UdpTransportTarget(ip_port, timeout=timeout, retries=retries)
        # 实例化上下文对象
        self.context = ContextData()
        
    def get_child(self, metric_name, child_oid):
        # ObjectIdentity 类负责 MIB 对象的识别:

        # 方法1: 指定要查询的 OID 对象或名称
        # node_oid = self.oid_map[metric_name]['node_oid']
        # oid = ObjectIdentity(f'{node_oid}.{child_oid}')
        
        # 方法2: 通过oid名字查询
        oid = ObjectIdentity('SNMPv2-MIB', metric_name, child_oid)

        # 使用 ObjectType 类初始化查询对象:
        obj = ObjectType(oid)
        # 使用 getCMD 方法进行查询，返回结果是一个迭代器, 需要使用 next() 来取值
        # 传递的参数均为为上面定义的变量, 以 v2c 为例(如果是 v3，communityData 替换为 userData)
        g = getCmd(self.engine, self.communityData, self.target, self.context, obj)

        # 取值
        errorIndication, errorStatus, errorIndex, result = next(g)
        if int(errorStatus) != 0:
            log.error(errorIndication)
            log.error(errorStatus)
            log.error(errorIndex)
            return

        # 打印输出
        for i in result:
            log.info(f'111: {i}')


    def walk(self, metric_name):
        """
        这个函数是查询接口列表, 和上面查询 sysName 的区别是使用了 nextCmd 来获取一个 MIB 子树的全部内容
        主要是 `lexicographicMode=False` 参数, 默认为 `True`, 会一直查询到 MIB 树结束.
        """
        # 方法1: 指定要查询的 OID 对象或名称
        # node_oid = self.oid_map[metric_name]['node_oid']
        # oid = ObjectIdentity(node_oid)

        # 方法2: 通过oid名字查询
        oid = ObjectIdentity('SNMPv2-MIB', metric_name)

        # 使用 ObjectType 类初始化查询对象:
        obj = ObjectType(oid)
        # 传递的参数均为为上面定义的变量, 以 v2c 为例(如果是 v3，communityData 替换为 userData)
        g = nextCmd(self.engine, self.communityData, self.target, self.context, obj, lexicographicMode=False)
        # 手动迭代并输出内容，并进行迭代器终止的判断
        try:
            while True:
                errorIndication, errorStatus, errorIndex, varBinds = next(g)
                #  (Pdb) errorStatus.namedValues.getName('noError')
                #  (Pdb) errorStatus.namedValues.getName(0)
                if int(errorStatus) != 0:
                    log.error(errorIndication)
                    log.error(errorStatus)
                    log.error(errorIndex)
                    return
                for iface in varBinds:
                    value = str(iface._ObjectType__args[1])
                    human_read_value = self.oid_map[metric_name]['dictionary'].get(value, value)
                    log.info(f'222: {iface} ({human_read_value})')
        except StopIteration:
            pass

    def get_or_walk(self, metric_name):
        child_oid = self.oid_map.get(metric_name, {}).get('child_oid', '')

        if child_oid:
            log.info(f'get_child metric: "{metric_name}"')
            self.get_child(metric_name, child_oid)
        else:
            log.info(f'walk metric: "{metric_name}"')
            self.walk(metric_name)


def get_target_ips() -> list:
    ips = []
    redis = get_redis()
    auth_key = "hash:probe_nas_name_to_nas_ip:auth"
    for nas in redis.hgetall(auth_key).values():
        ips.append(json.loads(nas)['ip'])
    return ips


def main():
    for ip in get_target_ips():
        try:
            mib = Mib(ip=ip, port=161)
            metrics = [
                'hh3cLswSysCpuRatio',
                # 'system',
                # 'sysName',
                # 'ifDescr',
                # 'ifOperStatus',
                # 'ifHCInOctets',
                # 'ifHCOutOctets',
                # 'hh3cEntityExtCpuUsage',
                # 'hh3cEntityExtMemUsage',
                # 'hh3cLswSysCpuRatio',
                # 'hh3cLswSysMemoryRatio'
            ]
            for metric in metrics:
                mib.get_or_walk(metric)
        except Exception as e:
            log.critical(traceback.format_exc())
            sentry_sdk.capture_exception(e)



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

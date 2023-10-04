"""
ac配置参考:
    https://www.sohu.com/a/496535833_99906077
    https://zhiliao.h3c.com/questions/dispcont/232042
    https://juejin.cn/post/6988416254646157320
"""

# 导入高层 API
from pysnmp.hlapi import SnmpEngine, CommunityData, UsmUserData, usmHMACMD5AuthProtocol, \
    usmAesCfb128Protocol, UdpTransportTarget, ContextData, ObjectIdentity, ObjectType, \
    getCmd, nextCmd
from settings import log, COMMUNITY_NAME


class Mib(object):
    oid_map = {
        'sysName': '1.3.6.1.2.1.1.5.0',
        'ifOperStatus': '1.3.6.1.2.1.2.2.1.8',
    }

    def __init__(self):
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
        ip_port = ('119.131.148.169', 161)
        self.target = UdpTransportTarget(ip_port)
        # 实例化上下文对象
        self.context = ContextData()
        
    def get(self, metric_name):
        # ObjectIdentity 类负责 MIB 对象的识别:

        # 方法1: 指定要查询的 OID 对象或名称
        _id = self.oid_map[metric_name]
        log.info(f'get metric: {metric_name}, id: {_id}')
        oid = ObjectIdentity(_id)
        
        # 方法2: 通过oid名字查询
        #  oid = ObjectIdentity('SNMPv2-MIB', 'sysName', 0)

        # 使用 ObjectType 类初始化查询对象:
        obj = ObjectType(oid)
        # 使用 getCMD 方法进行查询，返回结果是一个迭代器, 需要使用 next() 来取值
        # 传递的参数均为为上面定义的变量, 以 v2c 为例(如果是 v3，communityData 替换为 userData)
        g = getCmd(self.engine, self.communityData, self.target, self.context, obj)

        # 取值
        errorIndication, errorStatus, errorIndex, result = next(g)

        # 打印输出
        for i in result:
            log.info(i)


    def get_all(self, metric_name):
        """
        这个函数是查询接口列表, 和上面查询 sysName 的区别是使用了 nextCmd 来获取一个 MIB 子树的全部内容
        主要是 `lexicographicMode=False` 参数, 默认为 `True`, 会一直查询到 MIB 树结束.
        """
        # 方法1: 指定要查询的 OID 对象或名称
        _id = self.oid_map[metric_name]
        log.info(f'get metric: {metric_name}, id: {_id}')
        oid = ObjectIdentity(_id)

        # 方法2: 通过oid名字查询
        #  oid = ObjectIdentity('SNMPv2-MIB', 'ifDescr')

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
                if str(errorStatus) != 'noError':
                    log.error(errorIndication)
                    log.error(errorStatus)
                    log.error(errorIndex)
                    continue
                for iface in varBinds:
                    log.info(iface)
        except StopIteration:
            log.info('Get interface list done.')



if __name__ == "__main__":
    mib = Mib()
    mib.get('sysName')
    log.info('============================')
    mib.get_all('ifOperStatus')

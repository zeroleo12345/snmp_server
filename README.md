## NMS
实现 Network Management Station (NMS)

1. 监听UDP 162端口接收trap消息

2. 向远端UDP 161端口发送snmp消息


## Reference
https://pysnmp.readthedocs.io/en/latest/examples/v1arch/asyncore/manager/ntfrcv/transport-tweaks.html


## Download mib
https://mibs.thola.io/pysnmp/


## Client Simulator in Docker
- Install
```
yum install net-snmp-utils
```

- Send
```
snmptrap -v 2c -c public 127.0.0.1 "aaa" 1.3.6.1.4.1.2345 SNMPv2-MIB::sysLocation.0 s "just here" 
```


## get devices ips
```
hset hash:nas_name_to_nas_ip:auth 10.13.0.11 161
```

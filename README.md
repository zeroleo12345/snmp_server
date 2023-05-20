## NMS
实现 Network Management Station (NMS)
UDP 161端口接收snmp消息
UDP 162端口接收trap消息


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

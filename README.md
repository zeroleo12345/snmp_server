
## Download mib
https://mibs.thola.io/pysnmp/


## Client Simulator
- Install
```
yum install net-snmp-utils
```

- Send
```
snmptrap -v 2c -c public 127.0.0.1 "aaa" 1.3.6.1.4.1.2345 SNMPv2-MIB::sysLocation.0 s "just here" 
```

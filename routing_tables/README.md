# 路由表文件存放目录

将大核心交换机导出的路由表文件放在此目录。

## 文件命名规范

建议按以下格式命名：
```
S064-CORE-01-YYYYMMDD.csv
S064-CORE-02-YYYYMMDD.csv
S064-CORE-FHZB-YYYYMMDD.csv
```

## 文件格式

空格分隔的文本格式（`display ip routing-table` 导出）：
```
Destination/Mask    Proto   Pre  Cost      Flags NextHop         Interface
10.1.0.0/16         OSPF    10   2         D     10.0.2.1        Vlanif303
10.3.0.0/16         OSPF    10   2         D     10.0.3.1        Vlanif304
172.16.0.0/12       BGP     255  0         D     10.0.10.1       10GE4/0/4
```

## 注意事项

1. 程序会自动读取目录下所有 `.csv` 文件
2. 多台设备的路由会自动合并去重
3. 互联端口和非关注区域的路由会自动丢弃
4. 保留最新的路由表即可，旧文件可删除或归档

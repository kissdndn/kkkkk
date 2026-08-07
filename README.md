# 银行内网网络配置生成器 v1.0

根据源/目的IP和端口自动生成多厂商网络设备配置脚本。

## 功能特性

- **自动区域识别**：通过大核心交换机路由表匹配IP所属区域
- **策略矩阵驱动**：根据安全规范自动判断控制级别和配置设备
- **多厂商支持**：华为防火墙/H3C防火墙/Cisco ASA/华为交换机/H3C交换机
- **模块化地址表达**：明细IP / 新建Address-set / 存量Address-set 可选
- **批量输入支持**：单个IP、CIDR网段、IP范围混合输入
- **离线运行**：完全内网环境可用

## 项目结构

```
network_config_generator/
├── main.py                 # 主程序入口
├── config/
│   ├── zones.yaml         # 区域-设备映射配置
│   ├── port_map.yaml      # 大核心交换机端口映射表
│   └── policy_matrix.py   # 策略矩阵
├── core/
│   ├── ip_parser.py       # IP地址翻译模块
│   ├── route_parser.py    # 路由表解析器
│   ├── path_engine.py     # 路径决策引擎
│   └── config_gen.py      # 配置生成器
├── templates/             # Jinja2配置模板
│   ├── huawei_fw.j2      # 华为防火墙
│   ├── h3c_fw.j2         # H3C防火墙
│   ├── cisco_fw.j2       # Cisco ASA
│   ├── huawei_sw.j2      # 华为交换机
│   └── h3c_sw.j2         # H3C交换机
├── routing_tables/       # 路由表文件存放目录
│   └── README.md
├── requirements.txt      # Python依赖清单
├── prepare_packages.py   # 外网准备离线包
└── install_offline.py    # 内网离线安装
```

## 安装步骤

### 方式一：有互联网环境

```bash
pip install -r requirements.txt
```

### 方式二：内网离线安装（推荐）

1. **外网准备**：
   ```bash
   python prepare_packages.py
   ```

2. **拷贝到内网**：
   - 将整个项目文件夹 + `packages/` 文件夹拷贝到内网

3. **内网安装**：
   ```bash
   python install_offline.py
   ```

## 使用步骤

### 1. 准备路由表

将三台大核心交换机导出的路由表放入 `routing_tables/` 目录：

```
routing_tables/
├── S064-CORE-01-20260807.csv
├── S064-CORE-02-20260807.csv
└── S064-CORE-FHZB-20260807.csv
```

路由表格式（`display ip routing-table` 导出）：
```
Destination/Mask    Proto   Pre  Cost      Flags NextHop         Interface
10.1.0.0/16         OSPF    10   2         D     10.0.2.1        Vlanif303
```

### 2. 修改配置

编辑 `config/` 下的配置文件：

- **zones.yaml**：区域-设备映射（根据实际设备信息修改）
- **port_map.yaml**：端口映射表（从端口明细表导入）

### 3. 运行程序

```bash
python main.py
```

按提示完成5步流程：
1. **基础输入**：输入源IP、目的IP、端口、协议
2. **路径分析**：自动识别区域、判断路径、确定控制级别
3. **地址表达**：为每台设备选择明细/新建/存量模式
4. **命名规则**：确认规则名称
5. **生成配置**：输出可直接粘贴到设备的配置脚本

## 支持的输入格式

### IP地址
- 单个IP：`10.1.5.100`
- CIDR网段：`10.1.0.0/24`
- IP范围：`10.1.5.1-10.1.5.5`
- 混合输入：`10.1.5.100, 10.1.0.0/24, 10.1.5.1-10.1.5.5`

### 端口
- 单个端口：`443`
- 多个端口：`80, 443, 8080`

## 配置模板说明

### 华为防火墙 (USG6630E/USG6635F)
- 使用 `security-policy` 视图
- 支持 `ip address-set` 和 `ip service-set`
- 方向自动判断：inside→outside / outside→inside

### H3C防火墙 (SECPATH F5010)
- 使用 `acl advanced name` 格式
- 支持多IP/端口笛卡尔积生成

### Cisco ASA (5525)
- 使用 `object-group` + `access-list extended`
- 支持网络对象组和服务对象组

### 交换机ACL
- 华为CE16808：`acl name XXX advance`
- H3C S10506/S6730：`acl advanced name XXX`

## 注意事项

1. **增量配置**：本程序生成增量配置片段，需人工检查序号冲突
2. **存量对齐**：如需自动对齐存量配置，请提供设备当前配置快照
3. **灾备区域**：涉及灾备的访问统一在灾备防火墙配置
4. **连总区域**：连总侧不生成配置，只在分行端防火墙配置

## 版本历史

- v1.0 (2026-08-07)：初始版本，支持5步模块化流程

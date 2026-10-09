# Spark启动后无显示信号：2026-10-09

状态：用户确认画面恢复；2026-10-09 11:57 CST远端只读核验通过。当前显示配置已持久保留。
中断的实验仍保持停止，不在本次显示配置确认中自动恢复损坏的旧队列。

## 已恢复配置及长期约定

- `/etc/X11/xorg.conf`已移出生效路径；原配置保存在
  `/etc/X11/xorg.conf.sii-backup-20261009`，SHA与原件一致：
  `794ba039ae3fd03aef2097cf7b5015da9b74f292c23c7042d3f93ee694490b33`。
- Xorg自动探测真实连接，当前`USB-C-1 connected primary 2560x1440`、59.95Hz，
  物理尺寸597×336mm；HDMI-0实际未连接。因此此前HDMI的EDID报错不等于当前使用的
  USB-C显示器损坏。旧配置强制错误输出，停用后画面恢复，是本次修复的直接证据。
- 这是磁盘配置状态的持久改变，不是只在本会话生效的xrandr切换。为保留用户桌面，
  没有额外重启测试；不承诺任何未来线缆/硬件故障都不会再出现。
- 用户明确要求保持此配置。仓库`AGENTS.md`已加入显示保护约定：实验/渲染不得恢复旧
  headless配置、强制HDMI或更改桌面/驱动/GRUB。端口名与模式由自动探测决定，不硬编码。
- 服务器共享说明：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/display_recovery_20261009/DISPLAY_CONFIGURATION_PRESERVED_1157.md`。

下面保留故障发生时的排查记录；其中“尚未应用”描述当时状态，不代表当前修复未完成。

主机 `arm1@192.168.31.70`（`spark-4eb4`）。用户报告NVIDIA启动画面后黑屏、显示器无信号；
风扇仍转。11:44–11:49 CST多次SSH成功，GNOME/GDM正常运行，故至少当前不是整机关机。
系统记录11:37、11:38、11:40、11:41、11:43多个启动；原因未确认，不能由重启时间直接
断言是训练造成，也不能断言与训练无关。未执行远程reboot、驱动安装或内核/GRUB修改。

## 已读取的证据

- `/sys/class/drm/card1-HDMI-A-1/status` 为 `disconnected`，EDID为0字节。
- 内核重复 `nvidia-modeset: Unable to read EDID for display device HDMI-0`。
- `/etc/X11/xorg.conf`强制 `ConnectedMonitor DFP-0`、`VirtualHeads 1` 和
  `MetaModes HDMI-0: 1600x900 +0+0`，注释为headless配置。Xrandr由此报告connected，
  显示器尺寸却为0×0；不能将这个forced connected当作真实线缆连接证据。
- 配置mtime和ctime均为2026-07-27 15:07:17 CST，SHA256
  `794ba039ae3fd03aef2097cf7b5015da9b74f292c23c7042d3f93ee694490b33`。
  GRUB的mtime/ctime也为7月27日；不是本轮10月8/9日写入的配置。
- 当前启动内核检查未发现OOM、Xid或热关机记录；启动GPU热区44°C。
  这是读取范围内的阴性证据，不是硬件/历史故障排除证明。
- 11:47 CST通过xrandr临时切至1024×768/60Hz，命令成功，用户确认仍黑屏。
- `sudo -n -l`提示需要密码。未索取或保存用户密码，尚未停用系统Xorg配置或重启GDM。

## 已准备的可回滚修复

`tools/repair_spark_display_20261009.sh`仅允许该主机与上述配置hash：
将原文件移到 `/etc/X11/xorg.conf.sii-backup-20261009`（不覆盖已有文件），同步磁盘，
重启GDM以让Xorg自动探测显示器。`--rollback`可恢复原文件；重启失败时也尝试恢复。
这会退出当前桌面会话；不重启整机、不装驱动、不改GRUB，不启动实验。
命令成功仍需物理显示器确认；HDMI线、转接器、输入源或端口故障仍可能存在。

服务器脚本归档目标为
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/display_recovery_20261009/`，
实际上传/校验状态见UPDATE_LOG，不能仅凭本段目标路径认为已经应用修复。

## 实验影响

上一轮15小时384回合的最终报告SHA `fc62b5dba0b90b7e2f8f9cffbca5988c73206ca12a0024246c43c4ade77512b3`
和最终执行收据SHA `267aaeb2b3dc6db07c23ffd258ce9a76de0ce308e6cc5d36ddeecca633794f27`仍匹配。
这是两个交付文件的检查，不是重启后重新核验全部大轨迹。

新补强run `baseline_strengthening_20261009_0334`在11:39启动后被重启打断，
多份新job/config/log文件为0字节，旧execution仍可能写running。不能视为稳定运行，不能覆盖重试。
11:44和11:46实际检查本轮systemd单元/训练进程均不存在，停止指令返回unit not loaded。
保留现场，在服务器显示及运行稳定前不派发新实验。参数映射数值验证与本地18模型同数据审计
已通过；这些不是新闭环结果。恢复研究时必须新建attempt，核对源/hash、资源和中断证据。

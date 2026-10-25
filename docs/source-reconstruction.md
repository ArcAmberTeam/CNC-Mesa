# 烛龙 V2 源码与重建依据

已取得 Mesa 官方 HostMot2 源码，可进行二次开发。供应商的定制工程尚未取得，当前属于基于官方源码的重建，不是从位流恢复出的原始 HDL。

## 文件位置

| 位置 | 内容 |
| --- | --- |
| hostmot2/upstream/ | 官方 7i92.zip 内嵌 hostmot2.zip 的完整源文件快照，包括 VHDL、UCF、ISE 工程和软核汇编源码压缩包 |
| firmware/zhulong-v2/PIN_ZHULONG_V2_34.vhd | 按供应商引脚表重建的 34 路 GPIO 功能与模块数量 |
| mesa/board/zhulong-v2.json | FPGA 型号、板卡选择、回零开关 GPIO、方向与退开距离 |
| mesa/firmware/original/ | 原始 .bit 及供应商烧录说明，未经修改 |
| linuxcnc/vendor-reference/ | 原始六轴 INI/HAL 参考配置，未经修改 |
| homing/ | LinuxCNC 实时回零模块 |
| docs/hardware/ | 原始板卡文档与接口图 |
| docs/provenance/ | 原始文件校验清单和位流比较记录 |

## 已确认和未确认

- 原文件是 Xilinx .bit 容器，头部为 TopEthernetHostMot2.ncd;UserID=0x00007192、6slx9tqg144；配置载荷 340884 字节。这些头字段不能证明 PCB 引脚兼容性。
- 官方 seveni92.xise 对应 XC6SLX9、TQG144 和同一顶层实体。原包的顶层源码当前选中 7i98，因此准备工具明确换成 i92_x9card 与 PIN_ZHULONG_V2_34。
- 与同一官方包内 46 份 .bit 的配置载荷逐一比较，无相同项。因此不能声称找到供应商原工程或做到了位流一致复现。
- 重建引脚功能：0–3 为两个 Smart Serial 通道；4–15 为六路 STEP/DIR；16 为 PWM；17–24 为普通 GPIO；25–33 为三个编码器。五轴可使用六路中的五路。
- 20/21/22 是 HostMot2 GPIO 编号，对应 X/Y/Z 回零输入。用户最新确认常闭接 GND，未触碰导通、触碰后断开，取代先前“低电平触发”的说法。目标机只读观察为静止 `.in=FALSE`、触发 `TRUE`、释放 `FALSE`，因此配置使用 `.in`（`active_low=false`）；物理轴标识验证状态见接入交接文档。回零方向 X−、Y+、Z−。
- 官方 7i92.ucf 是候选物理引脚约束。烛龙 V2 的 FPGA 焊盘连接、振荡器、以太网控制器、Flash 接线和芯片速度等级仍须通过原理图、芯片标记或实测核对，尚未标为已验证。

## 二次开发与编译

运行 make prepare-firmware，生成 .build/firmware/zhulong-v2.xise。用支持 Spartan-6 的 Xilinx ISE 打开，执行综合、实现、时序检查与生成编程文件。准备工具没有烧录步骤。

StepGen 源码已在库内，hostmot2.vhd 根据 ModuleID 组合各实例，kubstepgen 系列文件实现步进脉冲逻辑。步宽、步间隔、方向建立/保持时间等还由 LinuxCNC 的 HostMot2 驱动寄存器配置，需验证实际引脚脉冲与参数一致。

位流经过综合、映射和布局布线后，不保留原始变量名、注释和 HDL 层次。当前只读取 .bit 头和配置载荷，未声称反编译得到了原始 VHDL；已有官方 HDL 可用于功能重建。

完整 ISE 综合、布局布线、时序收敛、烧录和板上验证尚未执行。GHDL 板卡配置断言只验证逻辑映射，不验证完整 FPGA 时序或 PCB 电气连接。

## 模块边界

firmware 通过 seveni92.xise 源文件清单组合 HostMot2，并替换顶层选择和板卡 PIN 包，生成文件仅进入 .build。这个依赖 Mesa 原生工程布局的适配器是明确的边界例外，其他代码不直接改写快照。

mesa_firmware 是只读位流分析的公共 Python 入口。包不依赖应用，测试和工具不得导入其私有文件。homing 的公共运行接口是 LinuxCNC HOMEMOD API，内部沿用 LinuxCNC 回零状态机和坐标更新方法。

## 来源与许可证

- [Mesa 官方 7i92 包](https://mesanet.com/software/parallel/7i92.zip)。下载包与每个源文件的 SHA-256 位于 hostmot2/manifest.json。
- [LinuxCNC HostMot2 源码仓库说明](https://github.com/LinuxCNC/hostmot2-firmware)。该历史仓库已归档，说明 Mesa 提供各板卡的源代码与位流。
- Mesa VHDL 保留原始版权和 GPLv2 或更新版本 / BSD 三条款双许可证说明，各文件按原有许可证使用；供应商手册、图片、位流的权利归原权利人。
- 回零模块基于 LinuxCNC GPLv2 代码，来源和修改范围位于 homing/provenance.json。本仓库不对第三方素材重新授权。

配置文件：`./mesa/board/zhulong-v2.json`，用于配置 FPGA 型号、工程来源和回零输入。

回零配置：`./linuxcnc/homing.json`，用于填写实测行程和回零速度；安装与启动见 `./docs/homing.md`。

工程准备：`make prepare-firmware`，生成 `./.build/firmware/zhulong-v2.xise`，用 Xilinx ISE 打开。

检查方式：`make check`；VHDL 检查：`make test-hdl`（需要 GHDL）。

源码说明：`./docs/source-reconstruction.md`。

# 回零

输入 20/21/22 分别对应 X/Y/Z，通过 in_not 将低电平触发转换为 HAL 有效信号，经过 5 个伺服周期去抖后，同时连接回零和对应方向的限位。

流程：X−、Y+、Z−方向寻找开关；触发后停止，退到距第一次触发位置向内 5 mm；慢速再次触发；向内退 5 mm，最终机床坐标为 0。退开距离由板卡配置的 homing.distance_mm 决定。实际重复精度取决于开关、去抖延迟与运动跟随误差。

LinuxCNC 标准回零第一次退开通常在开关释放后就停止，本模块改为完整的定长退开。第二次触发位置通过 HOME_OFFSET 设定，最终回到 HOME=0。轨迹、加减速、取消回零和坐标继续由 LinuxCNC 管理，FPGA 不绕过它独立发脉冲。

配置文件：linuxcnc/homing.json。search_speed_mm_s 为第一次寻找速度；latch_speed_mm_s 为第二次慢速寻找速度；return_speed_mm_s 为最终退回速度。usable_travel_from_switch_mm 是各轴从开关向内的实测可用总行程，尚未提供，保留 null。5 mm 退开距离不能当成总行程。生成器在两端各预留一个退开距离，再生成正负软限位。

安装与启动（LinuxCNC 2.9 开发环境）：

    make prepare-homing
    cd .build/homing
    sudo halcompile --install zhulong_homing.comp
    cd ../..
    # 填写 linuxcnc/homing.json 的实际行程后执行
    make prepare-linuxcnc
    linuxcnc .build/linuxcnc/烛龙V2.ini

准备和编译不启动机床、不触发回零。新配置保留供应商运动驱动参数，需要在现场核对；不会覆盖运行配置。HOME ALL 顺序为 X、Y、Z；A/B/C 未指定回零方法，排除在 HOME ALL 外。

验证通过公共 HOMEMOD 接口执行，使用 LinuxCNC 单轴轨迹规划器模拟运动，检查状态、距离、故障和取消。软件测试不代表实体机已完成回零验收。

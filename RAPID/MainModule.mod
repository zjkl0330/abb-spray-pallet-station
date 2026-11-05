MODULE MainModule
    !==========================================================
    ! 模块名  : MainModule
    ! 功能    : 喷涂 - 码垛复合工作站主控（批量换枪策略，6 件/批）
    ! 依赖    : SprayModule（tSpray / wobjSpray / SprayCycle）
    !           PalletModule（tGripper / PickAndPlace / nBoxCount）
    ! 说明    : 1) 采用"变量赋值法"切换工具，所有运动指令的工具参数
    !              统一用 tActive，禁止写死 tSpray / tGripper；
    !           2) pDockSpray / pDockGripper 为换枪位参考坐标，
    !              必须在 RobotStudio 中按换枪架模型重新示教；
    !           3) 批量值 6 受输送线缓存段容量限制，缓存段不足时取更小值。
    !==========================================================

    !---------- 当前工具（运行时可切换） ----------
    VAR tooldata   tActive;
    VAR num        nBatch := 6;      ! 每批处理件数

    !---------- 换枪位（相对 wobj0） ----------
    CONST robtarget pDockSpray :=
        [[-900,-600,900],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pDockGripper :=
        [[-900,-200,900],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pWaitHome :=
        [[0,0,900],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];

    !---------- 主程序 ----------
    PROC main()
        InitAll;
        tActive := tSpray;

        WHILE TRUE DO
            ! 等待启动
            WaitDI diCycleStart, 1;

            ! 安全回路检查（diSafetyOK = 1 为正常）
            IF diSafetyOK = 0 THEN
                SetDO doAlarmLamp, 1;
                TPWrite "Safety circuit open, cycle aborted.";
                EXIT;
            ENDIF

            ! 满盘处理：等待人工换盘后复位
            IF diPalletFull = 1 THEN
                SetDO doAlarmLamp, 1;
                TPWrite "Pallet full, please replace the pallet.";
                WaitDI diReset, 1;
                Reset doAlarmLamp;
                Reset doPalletFull;
                nBoxCount := 0;
            ENDIF

            ! 阶段 1：批量喷涂
            SprayBatch nBatch;

            ! 阶段 2：换夹爪
            ToolChangeToGripper;

            ! 阶段 3：批量码垛
            PalletBatch nBatch;

            ! 阶段 4：换回喷枪
            ToolChangeToSpray;

            ! 停止条件
            IF diCycleStop = 1 THEN
                EXIT;
            ENDIF
        ENDWHILE

        SetDO doRunLamp, 0;
        Stop;
    ENDPROC

    !---------- 批量喷涂 ----------
    ! 说明：等待工件入位放在循环开头，避免末次循环多等一次
    PROC SprayBatch(num nTimes)
        VAR num i;
        FOR i FROM 1 TO nTimes DO
            ! 等工件到喷涂位
            WaitDI diBoxAtSpray, 1;
            SetDO doConveyorRun, 0;         ! 停链
            SetDO doConveyorStop, 1;        ! 挡停定位
            WaitTime 0.3;

            ! 执行喷涂
            SprayCycle;

            ! 放行
            SetDO doConveyorStop, 0;
            SetDO doConveyorRun, 1;
            WaitTime 0.2;
        ENDFOR
    ENDPROC

    !---------- 批量码垛 ----------
    PROC PalletBatch(num nTimes)
        VAR num i;
        FOR i FROM 1 TO nTimes DO
            PickAndPlace;
        ENDFOR
    ENDPROC

    !---------- 换枪：喷枪 -> 夹爪 ----------
    PROC ToolChangeToGripper()
        MoveJ pWaitHome, v1000, fine, tActive \WObj:=wobj0;
        MoveJ pDockSpray, v500, fine, tActive \WObj:=wobj0;
        SetDO doToolChange, 1;              ! 请求换枪
        WaitDI diToolLocked, 1;             ! 等待锁紧到位
        WaitTime 0.5;
        Reset doToolChange;
        tActive := tGripper;                ! 切换 TCP，后续运动自动生效
        MoveJ pWaitHome, v800, fine, tActive \WObj:=wobj0;
    ENDPROC

    !---------- 换枪：夹爪 -> 喷枪 ----------
    PROC ToolChangeToSpray()
        MoveJ pWaitHome, v800, fine, tActive \WObj:=wobj0;
        MoveJ pDockGripper, v500, fine, tActive \WObj:=wobj0;
        SetDO doToolChange, 1;
        WaitDI diToolLocked, 1;
        WaitTime 0.5;
        Reset doToolChange;
        tActive := tSpray;
        MoveJ pWaitHome, v800, fine, tActive \WObj:=wobj0;
    ENDPROC

    !---------- 初始化 ----------
    PROC InitAll()
        Reset doConveyorRun;
        Reset doConveyorStop;
        Reset doSprayFan;
        Reset doSprayValve;
        Reset doVacuum;
        Reset doBlowOff;
        Reset doToolChange;
        Reset doAlarmLamp;
        Reset doPalletFull;
        SetDO doRunLamp, 1;

        nLayer    := 1;
        nCol      := 1;
        nRow      := 1;
        nBoxCount := 0;
        tActive   := tSpray;
    ENDPROC

ENDMODULE

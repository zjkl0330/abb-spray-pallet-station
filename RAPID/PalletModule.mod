MODULE PalletModule
    !==========================================================
    ! 模块名  : PalletModule
    ! 功能    : 纸箱抓取与错缝码垛（3 列 x 4 行 x 5 层 = 60 箱/盘）
    ! 适用    : ABB IRB 4600-20/2.05 + IRC5，RobotStudio 6.x
    ! 说明    : 1) 偶数层沿 X 向偏移 nOffEven（半箱错缝），Y 向不偏移；
    !           2) 所有点必须在 RobotStudio 中按实际托盘模型示教；
    !           3) 过渡点高度必须高于垛顶 200 mm 以上，防止撞垛。
    !==========================================================

    !---------- 工具与工件坐标系 ----------
    PERS tooldata tGripper := [TRUE,[[0,0,180],[0,0,1,0]],
                               [5.5,[0,0,90],[1,0,0,0],0,0,0]];

    ! wobjPallet 原点 = 托盘上表面左下角
    PERS wobjdata wobjPallet := [FALSE,TRUE,"",
                                 [[-600,-1600,150],[1,0,0,0]],
                                 [[0,0,0],[1,0,0,0]]];

    !---------- 工艺参数 ----------
    CONST num nBoxL     := 350;    ! 纸箱 X 向尺寸
    CONST num nBoxW     := 250;    ! 纸箱 Y 向尺寸
    CONST num nBoxH     := 250;    ! 层高
    CONST num nColMax   := 3;      ! 每层列数
    CONST num nRowMax   := 4;      ! 每层行数
    CONST num nLayerMax := 5;      ! 层数
    CONST num nOffEven  := 125;    ! 偶数层 X 向错缝量（半箱）
    CONST num nPalletQty := 60;    ! 单盘总箱数

    !---------- 运行变量 ----------
    VAR num nLayer    := 1;
    VAR num nCol      := 1;
    VAR num nRow      := 1;
    VAR num nBoxCount := 0;

    !---------- 关键示教点 ----------
    ! 取料位：纸箱顶面中心上方（坐标系 wobjSpray，工件已停在取料位）
    CONST robtarget pPickAbove :=
        [[0,0,500],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pPick :=
        [[0,0,180],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];

    ! 托盘基准点：第 1 层第 1 列第 1 行箱位中心上方 300 mm
    CONST robtarget pPalletRef :=
        [[175,125,300],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];

    ! 过渡点：跨越输送链上方。注意 Z 应高于垛顶(1400)+200 = 1600
    CONST robtarget pTransit :=
        [[0,0,1650],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];

    !---------- 单件抓取与码放 ----------
    PROC PickAndPlace()
        ! --- 抓取 ---
        MoveJ pPickAbove, v800, z50, tGripper \WObj:=wobjSpray;
        MoveL pPick, v200, fine, tGripper \WObj:=wobjSpray;
        SetDO doVacuum, 1;
        WaitDI diVacuumOK, 1;                       ! 真空压力到位
        WaitTime 0.2;
        MoveL pPickAbove, v300, z20, tGripper \WObj:=wobjSpray;

        ! --- 跨越到托盘上方 ---
        MoveJ pTransit, v1000, z50, tGripper \WObj:=wobjPallet;
        MoveJ Offs(pPalletRef, FnXOff(), FnYOff(), FnZOff()),
              v800, z50, tGripper \WObj:=wobjPallet;

        ! --- 放料（Z 向落 300 mm 到箱面） ---
        MoveL Offs(pPalletRef, FnXOff(), FnYOff(), FnZOff()-300),
              v200, fine, tGripper \WObj:=wobjPallet;
        SetDO doVacuum, 0;
        SetDO doBlowOff, 1;                         ! 破真空吹气
        WaitTime 0.3;
        Reset doBlowOff;
        MoveL Offs(pPalletRef, FnXOff(), FnYOff(), FnZOff()-250),
              v300, z20, tGripper \WObj:=wobjPallet;

        ! --- 计数与确认 ---
        nBoxCount := nBoxCount + 1;
        SetDO doBoxPlaced, 1;
        WaitTime 0.1;
        Reset doBoxPlaced;
    ENDPROC

    !---------- 整盘码垛 ----------
    PROC PalletizeCycle()
        nBoxCount := 0;
        FOR nLayer FROM 1 TO nLayerMax DO
            FOR nRow FROM 1 TO nRowMax DO
                FOR nCol FROM 1 TO nColMax DO
                    PickAndPlace;
                ENDFOR
            ENDFOR
        ENDFOR
        SetDO doPalletFull, 1;
        SetDO doAlarmLamp, 1;
        TPWrite "Pallet full, box count = " \Num:=nBoxCount;
    ENDPROC

    !---------- 偏移计算 ----------
    ! X 向：奇偶层错缝
    FUNC num FnXOff()
        IF nLayer MOD 2 = 1 THEN
            RETURN (nCol - 1) * nBoxL;
        ELSE
            RETURN (nCol - 1) * nBoxL + nOffEven;
        ENDIF
    ENDFUNC

    ! Y 向：不区分奇偶层
    FUNC num FnYOff()
        RETURN (nRow - 1) * nBoxW;
    ENDFUNC

    ! Z 向：随层数抬升
    FUNC num FnZOff()
        RETURN (nLayer - 1) * nBoxH;
    ENDFUNC

ENDMODULE

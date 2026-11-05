MODULE SprayModule
    !==========================================================
    ! 模块名  : SprayModule
    ! 功能    : 纸箱表面喷涂（顶面 3 道 + 前侧面 + 右侧面）
    ! 适用    : ABB IRB 4600-20/2.05 + IRC5，RobotStudio 6.x
    ! 说明    : 1) 所有点位以 wobjSpray 为基准，坐标为参考值，
    !              必须在 RobotStudio 中按实际模型重新示教；
    !           2) 真机喷涂须改用防爆机型（IRB 52 / IRB 5500），
    !              本模块仅用于运动学仿真与节拍验证。
    !==========================================================

    !---------- 工具与工件坐标系 ----------
    PERS tooldata tSpray := [TRUE,[[0,0,220],[0,0,1,0]],
                             [4,[0,0,120],[1,0,0,0],0,0,0]];

    ! wobjSpray 原点 = 喷涂工位纸箱底面中心
    PERS wobjdata wobjSpray := [FALSE,TRUE,"",
                                [[900,0,700],[1,0,0,0]],
                                [[0,0,0],[1,0,0,0]]];

    !---------- 示教点（相对 wobjSpray） ----------
    CONST robtarget pSprayHome :=
        [[0,0,900],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pSprayApproach :=
        [[0,0,650],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];

    CONST robtarget pTop1 :=
        [[-140,-90,400],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pTop2 :=
        [[-140, 90,400],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pTop3 :=
        [[   0, 90,400],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pTop4 :=
        [[   0,-90,400],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pTop5 :=
        [[ 140,-90,400],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pTop6 :=
        [[ 140, 90,400],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];

    CONST robtarget pSide1 :=
        [[0,-275,125],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pSide2 :=
        [[350,-275,125],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pSide3 :=
        [[325,0,125],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pSide4 :=
        [[325,250,125],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];

    !---------- 喷涂主例程 ----------
    ! 前置条件：工件已在喷涂工位停位（diBoxAtSpray = 1）
    PROC SprayCycle()
        ! 1. 快速接近，切换为直线下枪
        MoveJ pSprayHome, v1000, fine, tSpray \WObj:=wobjSpray;
        MoveJ pSprayApproach, v800, z50, tSpray \WObj:=wobjSpray;

        ! 2. 先开雾化空气，建立稳定漆雾后再开涂料阀
        SetDO doSprayFan, 1;
        WaitTime 0.3;

        ! 3. 顶面第 1 道
        MoveL pTop1, v150, fine, tSpray \WObj:=wobjSpray;
        SetDO doSprayValve, 1;
        MoveL pTop2, v150, z5, tSpray \WObj:=wobjSpray;

        ! 4. 顶面第 2 道（反向蛇形，保证漆膜均匀）
        MoveL pTop3, v150, z5, tSpray \WObj:=wobjSpray;
        MoveL pTop4, v150, z5, tSpray \WObj:=wobjSpray;

        ! 5. 顶面第 3 道
        MoveL pTop5, v150, z5, tSpray \WObj:=wobjSpray;
        MoveL pTop6, v150, z5, tSpray \WObj:=wobjSpray;

        ! 6. 前侧面：先关阀移位，到起点再开阀，避免过喷
        SetDO doSprayValve, 0;
        MoveL pSide1, v300, fine, tSpray \WObj:=wobjSpray;
        SetDO doSprayValve, 1;
        MoveL pSide2, v150, z5, tSpray \WObj:=wobjSpray;

        ! 7. 右侧面
        SetDO doSprayValve, 0;
        MoveL pSide3, v300, fine, tSpray \WObj:=wobjSpray;
        SetDO doSprayValve, 1;
        MoveL pSide4, v150, z5, tSpray \WObj:=wobjSpray;

        ! 8. 关阀后保持雾化空气 0.3 s，吹净喷嘴残漆
        SetDO doSprayValve, 0;
        WaitTime 0.3;
        SetDO doSprayFan, 0;

        ! 9. 退枪回安全原点
        MoveL pSprayApproach, v500, z50, tSpray \WObj:=wobjSpray;
        MoveJ pSprayHome, v1000, fine, tSpray \WObj:=wobjSpray;

        ! 10. 输出完成信号（脉冲 0.2 s）
        SetDO doSprayDone, 1;
        WaitTime 0.2;
        Reset doSprayDone;
    ENDPROC

ENDMODULE

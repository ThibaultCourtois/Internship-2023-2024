MODULE WAAM
    PROC main()
        ConfL \Off;
        SetDO arctoggle, 0;
        MoveAbsJ [[0, 0, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]],v50 ,fine, PieceBase; 
        MoveAbsJ [[0, 6, 31, -10, -37, 8], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]],v50 ,fine, PieceBase; 
        MoveL [[0, 0, -100], [1, 0, 0, 0], conf, extj],v50 ,fine, PieceBase \WObj:=Torch;
       TransitionPiece1;
        MoveL [[0, 0, -100], [1, 0, 0, 0], conf, extj],v50 ,fine, PieceBase \WObj:=Torch;
        MoveAbsJ [[0, 6, 31, -10, -37, 8], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]],v50 ,fine, PieceBase; 
        MoveAbsJ [[0, 0, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]],v50 ,fine, PieceBase; 
    ENDPROC
ENDMODULE
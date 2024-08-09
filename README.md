WAAM Process Description

This notice is meant to help you understand and use the current WAAM IndexLab by describing the calibration process, the RobotStudio simulation (and thus the real process), and the parameters I used to print my best piece.

I have created a GitHub repository where you can find my WAAM RobotStudio simulation as well as my Python algorithm for post-processing Prusa Slicer files for a standard Prusa plastic 3D printer.
RobotStudio Simulation and Real Process

The WAAM RobotStudio simulation I am using is a perfect reproduction of reality in terms of robot path, signal sending, etc. If you need to learn RobotStudio, I have created a guide available in the GitHub repository.
Coordinate Systems

The simulation is based on two important frames: the TCP frame (tool frame) and the Torch frame (work object frame). Inside the IndexLab ABB robot controller, I have already registered my tool called PieceBase (which includes the 90° tool attachment and a small disk bed for WAAM) and the Torch frame in the USER module, which is a system module. Every data inside a system module can be used by every other module. I have also implemented a PrintedCylinderTool inside the simulation and the real robot that I used to print on an already printed cylinder. In RobotStudio, you need ti swutch i's visual state to visible.

The robot executes the 3D plastic printer tool head movement in the torch coordinate system. However, it is the torch that actually deposits melted steel on the bed. Thus, the deposition is offset from the distance between the tool head and the origin of the printer, which in our case is the Torch work object plane.

Consequently, the TCP trace of the robot in RobotStudio is the offset and upside-down version of the slicing.
Calibration

To calibrate the robot TCP, I used the torch endpoint as a fixed calibrating stake. Use the orient and linear mode to perform the ABB calibration process (explained in my guide). What you want to calibrate is only the position of the origin of the TCP (the quaternion orientation is [1, 0, 0, 0]; you will need to edit the value of the orientation after calibration as it will always be close but not perfectly [1, 0, 0, 0]).

After calibrating the TCP, you need to calibrate the Torch frame. For this, you only calibrate the object frame (not the user one) by placing the center of the WAAM disk at the endpoint of the torch. As with the TCP, you will need to edit the orientation values to [1, 0, 0, 0].

Next, you will refine the torch calibration (it is more important than the TCP). To do this, jog the robot in linear mode near the torch endpoint. In linear mode, you can see the coordinates of the TCP in the coordinate system of your choice (choose the Torch frame). You then perform several checks:

    Is the center of the disk bed at X0, Y0 in torch coordinates? If not, edit the Torch declaration values of the work object coordinates.
    Is the extremity of the disk base at the correct XY coordinates? (For example, you should be at X30 / -30 or Y30 / -30 for a disk with a radius of 30 mm.)
    Adjust the Z coordinate as needed (I recommend at least 3 mm; otherwise, the filament might collide with your piece during printing).

During this process, use the increment jogging option to be precise. If you collide with the filament (this happens often), jog the robot away, set the arc-on signal to one to extrude, then cut it back to the desired length (you want to have between 15 and 17 mm between the end of the torch metal protection and the WAAM bed).
Main Interest of RobotStudio Simulation

A key feature of the RobotStudio simulation is the use of the TCP trace option in the simulation panel to visualize your print. To do this, switch the TCP trace color with the arctoggle signal to separate printing movements from normal positioning movements.
Signals

Signal list inside the ABB:

    arctoggle
    job1
    job2
    job3

The Fronius is connected to the IRC5 controller IO component. The small black case near the Fronius is the AI/IO V2 of Fronius, used to send and receive digital signals. Currently, four signals are set up: IN1 is the arctoggle digital output of the ABB, and IN2 to IN4 are job1 to job3 digital outputs of the ABB. Job1 to job3 are the bits of the binary job number of the Fronius TPS; switching their state will change the job program you are using inside the Fronius. Thus, you can switch between eight different welding job programs to create pieces with variable layer height, for example. Keep in mind that you need to set the Fronius to JOB mode to use this feature.

During a print, you can see the state of the signals with the FlexPendant and also with the LED of the AI/IO V2 black case.
Parameters
Fronius Parameters

You can find some interesting features to adjust by clicking on process parameters and then optimize job. Keep in mind that you need to change the job signals to switch jobs (this is not possible directly on the Fronius).

    First layer:
        Current: 120 A (FRONIUS optimize job parameters)
        Beginning current: 100%
        End current: 90%
        Slope 2: 0.5 s

    Second layer:
        Current: 90 A (other parameters are the same)

Robot Parameters

I used a speed of 14.2 mm/s for my print, corresponding to 850 mm/min for the WASP printer, which is adequate for WAAM. Speed is set constant during the print, even between the first and second layers.

You need to use a zone parameter in your movement command to reach this speed with a smooth path. I used the smallest predefined speed inside RobotStudio for this: z0, corresponding to a 0.3 mm radius. The problem is that when using zone parameters, the robot executes three instructions ahead of the pointer. This means that if you have some signal state switch instructions in your code, the robot might execute them before reaching the desired position (arc on before reaching the start position). Thus, the strategy is to use some fine (no zone data) before and after signal changes as well as WaitTime instructions with the \InPos argument to make the robot wait in the desired position. I used 0.75 s pauses, which gave me good results (refer to my simulation RAPID program to understand this).

The robot is not well fixed to the ground, so be careful about that.
Prusa Slicer Parameters

Of course, I don't expect you to use the same strategy and hope you will create a nice Grasshopper slicer that will dynamically change the wrist orientation of the robot to print some difficult shapes. However, I found some good parameters to perfectly fill a piece.

My layer height with my current parameters is approximately 1.5 mm. My line width is 1.5 mm, and I set a gap of 2 mm between my printed lines to fuse them. Thus, you print two parallel lines to create a 5 mm wide rectangle. With these parameters, your lines will fuse, and your shapes will be completely filled.

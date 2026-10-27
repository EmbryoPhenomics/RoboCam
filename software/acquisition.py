# Acquisition class instance for handling timelapse acquisitions
import time
import threading
import pandas as pd
import os
import datetime
import emails
import multiprocessing as mp
import threading
import cv2
import re
import gc

def to_list(vals):
    if not isinstance(vals, list):
        if isinstance(vals, float or int or str):
            vals = [vals]
        else:
            vals = list(vals)
    return vals

def pack_results(data):
    t_,c,a,i,tp,e,mft,lft,hft = map(to_list, data)
    d = dict(TotalTime=t_, AcquisitionTime=c, AncillaryTime=a, 
             IncompleteFrames=i, MeanFrameTime=mft, MinFrameTime=lft, MaxFrameTime=hft,
             Timepoint=tp, Embryo=e)
    df = pd.DataFrame(data=d)   
    return df

def send_email(email_cls, timepoint, data, paths):
    email = emails.Emails()
    email.login(email_cls.username, email_cls.password)

    try:
        if email.isLoggedIn:
            outfiles = [] 

            if isinstance(paths, list):
                for file in paths:
                    video = cv2.VideoCapture(file)
                    _, frame = video.read()
                    new_file = re.sub('.mkv', '.png', file)
                    cv2.imwrite(new_file, frame)
                    video.release()

                    outfiles.append(new_file)
            else:
                video = cv2.VideoCapture(paths)
                _, frame = video.read()
                new_file = re.sub('.mkv', '.png', paths)
                cv2.imwrite(new_file, frame)
                video.release()

                outfiles.append(new_file)

            text = f"""\
            LEC update: Timepoint {timepoint}

            No. of positions imaged: {len(paths)}

            See attached files for still images of positions at this timepoint."""

            email.send(f'LEC update: timepoint {timepoint}', text, outfiles)

            for file in outfiles:
                os.remove(file)
    finally:
        email.close()





class Acquisition:
    def __init__(self):
        self.acquiring = False

    def acquire(self, *args, **kwargs):
        '''
        Main acquisition loop for acquiring timelapse video at different XYZ positions

        Parameters
        ----------
        folder : str
            File path to folder in which to save video.
        positions : str
            Number of positions to acquire video for, either 'Single' or 'Multiple'. If
            'Single' then only the current position will be recorded, else the stage will 
            move between positions and capture video for each.
        timepoints : int
            Number of timepoints to iterate the acquisition loop over.
        interval : int or float
            Length of time between timepoints (minutes).
        capture_length : int or float
            Duration of video capture at each timepoint and each position (seconds).

        exposure : int or float
            Shutter speed in micro-seconds.
        fps : int or float
            Frame-rate of video capture
        sensor_mode : int
            Camera sensor mode index, this is specific to a given camera model and the sensor driver
            as to what modes are available. For more info check: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
            and section 4.2.2.3

        stage : Object
            Class instance of the Hardware class in the 'xyz' module for controlling the XYZ stage.
        leds : Object
            Class instance of the HardwareBrightness class in the 'leds' module for controlling LEDS brightness.
        light_auto_dim : bool
            Whether to dim lights between timepoints.

        exp_log : Object
            Class instance for recording information regarding acquisition progress.
        
        xyz_coords : Object
            XYZ coordinate class derived from 'xyz' module.

        email : Object
            Email class instance derived from 'email' module.

        '''
        print(args, kwargs)
        thread = threading.Thread(target=self._acquire, args=args, kwargs=kwargs)
        thread.start()

    def _video_capture_process(self, video_path, capture_length, exposure, fps, analogue_gain, sensor_mode=0):
        import camera_backend_picamera2
        picam2 = camera_backend_picamera2.Camera()
        print('STARTING CAPTURE')
        picam2.video_capture(video_path, capture_length, exposure, fps, analogue_gain, sensor_mode)
        picam2.close()
        return True

    def video_capture(self, video_path, capture_length, exposure, fps, analogue_gain, sensor_mode):
        """
        Run video capture in a separate process and monitor it.
        Restarts if stalled, up to N retries.
        """
        retries = 3
        for attempt in range(1, retries + 1):
            print(f"[INFO] Capture attempt {attempt}/{retries}")
            proc = mp.Process(
                target=self._video_capture_process, 
                args=(video_path, capture_length, exposure, fps, analogue_gain, sensor_mode),
                daemon=True)
            proc.start()

            start_time = time.time()
            max_time = capture_length + 20  # duration + grace

            while time.time() - start_time < max_time:
                time.sleep(5)
                if not proc.is_alive():
                    break
                # check for stalled file
                if os.path.exists(video_path):
                    size = os.path.getsize(video_path)
                    time.sleep(5)
                    new_size = os.path.getsize(video_path)
                    if new_size == size and (time.time() - start_time) > 30:
                        print("[WARN] Capture appears stalled; restarting process...")
                        proc.terminate()
                        proc.join(timeout=10)
                        break

            print('Is thread alive? ', proc.is_alive())

            if proc.is_alive():
                print("[WARN] Capture did not finish on time; killing process...")
                proc.terminate()
                proc.join(timeout=10)

            if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                return True  # success

            print(f"[INFO] Attempt {attempt} failed, retrying...")
            time.sleep(3)

        return False


    def _acquire(self,
        folder, positions, timepoints, interval, capture_length, # Acquisition parameters
        camera, exposure, fps, sensor_mode, analogue_gain, # Camera settings
        stage, leds, light_auto_dim, # Hardware instances and settings
        exp_log, # Ancillary instances
        xyz_coords, # XYZ coordinates
        email): # Email class

        self.shutdown = threading.Event()
        exp_log.clear()
        
        self.acquiring = True

        # Timelapse recording for a single position
        if positions == 'Single':
      
            # Grab current led value to change to during acquisition and switch off after each timepoint
            LED_VALUE = leds.current
            if not light_auto_dim:
                leds.set(0)

            time.sleep(1)

            x,y,z,label = xyz_coords.get_current()

            exp_log.startup([label], timepoints)
            
            paths = []
            for t in range(timepoints):
                t1_start = time.time()

                if self.shutdown.is_set():
                    self.acquiring = False
                    print('Exiting acquisition...')
                    return         

                print(f'Acquiring footage for timepoint {t+1}...')
                
                # Turn leds on
                leds.set(LED_VALUE)
                time.sleep(1)

                path = os.path.join(folder, f'{label}_timepoint{t+1}.mkv')
                paths.append(path)

                # Acquire footage
                t1 = time.time()
                success = self._video_capture_process(path, capture_length, exposure=exposure, fps=fps, analogue_gain=analogue_gain, sensor_mode=sensor_mode)
                t2 = time.time()

                if not success:
                    self.stop()
                    leds.set(LED_VALUE)
                    print('Exiting acquisition...')
                    return

                exp_log.update(label, t, str(datetime.datetime.fromtimestamp(t2)))
                exp_log.export(os.path.join(folder, 'time_data.csv'))

                # Turn leds off
                if not light_auto_dim:
                    leds.set(0) 

                # # Send progress updates
                # if email.isLoggedIn:
                #     email_proc = mp.Process(target=send_email, args=(email, t+1, zip(*[timepointData, ]), path))
                #     email_proc.start()

                t2_end = time.time()
                acqTime = t2_end - t1_start
                print(f'Sleep time: {interval*60 - acqTime}')
                sleep_time = interval*60 - acqTime
                
                for i in range(round(sleep_time)):
                    if self.shutdown.is_set():
                        leds.set(LED_VALUE)
                        self.acquiring = False
                        print('Exiting acquisition...')
                        return         
                    
                    time.sleep(1)    

        elif positions == 'Multiple':
            if interval == 0:
                raise ValueError('Cannot have no acquisition interval when acquiring footage for multiple positions.')

            labels = xyz_coords.labels
            xy_data = [dict(x=x, y=y, z=z) for x,y,z in zip(xyz_coords.xs, xyz_coords.ys, xyz_coords.zs)]

            # Grab current led value to change to during acquisition and switch off after each timepoint
            LED_VALUE = leds.current
            if not light_auto_dim:
                leds.set(0)

            time.sleep(1)

            # Creation of filepaths
            paths = {}
            for replicate in labels:
                paths[replicate] = []
                replicate_path = os.path.join(folder, replicate + '/')

                if not os.path.exists(replicate_path):
                    os.makedirs(replicate_path)

                for t in range(timepoints):
                    timepoint_path = os.path.join(replicate_path, f'timepoint{t+1}.mkv')
                    paths[replicate].append(timepoint_path)

            exp_log.startup(labels, timepoints)

            print('[INFO] Starting acquisition for multiple positions...')
            
            for t in range(timepoints):
                print(f'Acquiring footage for timepoint {t+1}...')

                # Turn leds on
                leds.set(LED_VALUE)
                time.sleep(1)
              
                t1_start = time.time()
                # timepointPaths = []
                # timepointData = []
                for label,pos in zip(labels, xy_data):
                    if self.shutdown.is_set():
                        self.acquiring = False
                        print('Exiting acquisition...')
                        return          
    
                    # Position move
                    x,y,z = (pos['x'], pos['y'], pos['z'])
                    stage.moveXY(x,y,z)

                    time.sleep(5) # Delay for 5 seconds before recording

                    # Acquire footage
                    path = paths[label][t]
                    # timepointPaths.append(path)

                    # Acquire footage
                    t1 = time.time()
                    success = self._video_capture_process(path, capture_length, exposure=exposure, fps=fps, analogue_gain=analogue_gain, sensor_mode=sensor_mode)
                    t2 = time.time()

                    if not success:
                        self.stop()
                        leds.set(LED_VALUE)
                        print('Exiting acquisition...')
                        return

                    exp_log.update(label, t, datetime.datetime.fromtimestamp(t1))

                exp_log.export(os.path.join(folder, 'time_data.csv'))

                # Turn leds off
                if not light_auto_dim:
                    leds.set(0)     

                # Send progress updates
                # if email.isLoggedIn:
                #     email_proc = mp.Process(target=send_email, args=(email, t+1, zip(*timepointData), timepointPaths))
                #     email_proc.start()

                t2_end = time.time()
                acqTime = t2_end - t1_start
                print(f'Sleep time: {interval*60 - acqTime}')
                sleep_time = interval*60 - acqTime
                
                for i in range(round(sleep_time)):
                    if self.shutdown.is_set():
                        leds.set(LED_VALUE)
                        self.acquiring = False                        
                        print('Exiting acquisition...')
                        return           
                    
                    time.sleep(1)    
                           
        leds.set(LED_VALUE)

        print('Completed acquisition.')
        # df = pack_results(zip(*time_data))
        # df.to_csv(os.path.join(folder, 'capture_data.csv'))

        # if email.isLoggedIn:
        #     text = f"""\
        #     LEC update: Completed acquisition.
        #     """

        #     email.login(email.username, email.password)
        #     email.send(f'LEC update: Completed acquisition.', text, None)
        #     email.close()

        self.stop()
        self.acquiring = False


    def stop(self):
        '''
        Stop acquisition loop if it's running.
        '''
        if self.acquiring:
            self.shutdown.set()
            
            
if __name__ == '__main__':
    from app import picam2, stage, leds, experimental_log, coord_data, email
    
    leds.set(20)
    stage.setOrigin()
    coords = [{'x': 10.0, 'y': 10.0, 'z': 0.0, 'label': 'Pos1'}, {'x': 20.0, 'y': 20.0, 'z': 0.0, 'label': 'Pos2'}]
    
    for coord in coords:
        x,y,z,l = coord.values()
        coord_data.xs.append(x)
        coord_data.ys.append(y)
        coord_data.zs.append(z)
        coord_data.labels.append(l)          

    kwargs = {'folder': '/home/pi/test', 'positions': 'Multiple', 'timepoints': 1000, 'interval': 1, 'capture_length': 5, 'camera': picam2, 'exposure': 20000, 'fps': 30, 'sensor_mode': 0, 'analogue_gain': 1, 'stage': stage, 'leds': leds, 'light_auto_dim': False, 'exp_log': experimental_log, 'xyz_coords': coord_data, 'email': email}

    acquisition = Acquisition()
    acquisition.acquire(**kwargs)

    time.sleep(1000)


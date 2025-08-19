import numpy as np
from gnuradio import gr
import pmt
import csv
from datetime import datetime
from scipy.signal import find_peaks

class blk(gr.sync_block):  
    def __init__(self, vec_size=2048, Nzc=61, RF=4, Node=1, filename="/home/student/Downloads/metadata.csv"):
        gr.sync_block.__init__(
            self,
            name='NodeIdentifier',  
            in_sig=[(np.uint8, vec_size), (np.complex64, vec_size)],
            out_sig=None
        )
        self.vec_size = vec_size  
        self.Nzc = Nzc
        self.RF = RF
        self.Sender_ID = Node
        self.packet_started = [False for _ in range(7)]
        self.filename = filename

        # Initialize CSV file
        try:
            with open(self.filename, 'a', newline='') as f:
                writer = csv.writer(f)
                if f.tell() == 0:
                    writer.writerow(["Sender_ID", "Receiver_ID", "Timestamp", "Received Power (dBm)"])
        except IOError:
            print(f"Error: Could not write to file {self.filename}")

    def calculate_rsrp(self, signal,non_zero_indices):
        signal = signal.flatten()
        len_sig = len(non_zero_indices)
        
        magnitude_squared = np.abs(signal[non_zero_indices[0]:non_zero_indices[0]+len_sig*self.RF*self.Nzc])**2
        
        rsrp_linear = np.mean(magnitude_squared) #Results may be smaller that actual RSRP, since some part of signal may not have any zc sequence but only noise
        rsrp_dbm = 10 * np.log10(rsrp_linear) if rsrp_linear > 0 else -np.inf
        return rsrp_dbm

    def get_current_timestamp(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    def start_packet(self, Receiver_ID, signal,non_zero_indices):
        Receiver_ID += 1  
        start_time = self.get_current_timestamp()
        rsrp_dbm = self.calculate_rsrp(signal,non_zero_indices)
        try:
            with open(self.filename, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([self.Sender_ID, Receiver_ID, start_time, f"{rsrp_dbm:.6f}"])
        except IOError:
            print(f"Error: Could not write to file {self.filename}")


    def work(self, input_items, output_items):
        in0 = input_items[0]  
        in1 = input_items[1]  

        non_zero_indices = np.nonzero(in0)[1]
        packet_detector = [False for _ in range(7)]

        if len(non_zero_indices) != 0:
            for i in range(len(non_zero_indices) - 1):
                if non_zero_indices[i + 1] > non_zero_indices[i]:
                    node_index = ((np.abs(non_zero_indices[i + 1] - non_zero_indices[i] - self.Nzc * self.RF) - self.RF) // self.RF) % 7
                    packet_detector[node_index] = True

            if sum(packet_detector) == 1:
                for i in range(len(packet_detector)):
                    if packet_detector[i] and not self.packet_started[i]:
                    
                        self.packet_started[i] = True
                        self.start_packet(i, in1,non_zero_indices)
            else:
                for i in range(len(self.packet_started)):
                    if self.packet_started[i]:
                        self.packet_started[i] = False
                return 1  

        for i in range(len(self.packet_started)):
            if self.packet_started[i] and len(non_zero_indices) == 0:
                self.packet_started[i] = False

        return len(in1)


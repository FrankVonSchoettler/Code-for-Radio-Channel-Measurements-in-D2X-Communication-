
import numpy as np
from gnuradio import gr
import time
import pmt

class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    """Embedded Python Block example - a simple multiply const"""

    def __init__(self,  inter_arrival_time_mean=100.0, tau=0.01, u=1, N=7, q=0):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='PacketPoissonGenerator',   # will show up in GRC
            in_sig = None,
            out_sig=[np.complex64]
        )
        self.u = u  # Root index of the ZC sequence
        self.N = N  # Length of the ZC sequence
        self.q = q  # Cyclic shift index        
        self.inter_arrival_time_mean = inter_arrival_time_mean
        self.time_to_next_packet = self.calculate_time_to_next_packet()        
        self.last_packet_time = time.time_ns()
        self.tau = tau
        self.packet_end_time = self.last_packet_time + tau * 1e9
        self.counter=0
        self.transmitting = False  # Current state of transmission
        self.ZC_sequence = self.generate_zc_sequence(self.u, self.N, self.q)
    def generate_zc_sequence(self, u, N, q):
        """
        Generate a Zadoff-Chu sequence.
        
        Parameters:
        u (int): Root index of the ZC sequence.
        N (int): Length of the ZC sequence.
        q (int): Cyclic shift index.
        
        Returns:
        np.array: Generated ZC sequence.
        """
        n = np.arange(N)
        zc_seq_origin = np.exp(-1j  * np.pi * u * n * (n + 1) / (N)) 
        zc_seq_node = np.exp(-1j  * np.pi * u * n * (n + 1 +2*q) / (N))
        #signal = np.arange(256)
        zc_seq = np.concatenate([zc_seq_origin,zc_seq_node], axis = 0)

        #zc_seq_conj = np.conj(zc_seq)
        #zc_zeros_padding = np.zeros(73)
        #zc_real_block = np.exp(-1j * 2 * np.pi * u * n * (n + 1 + 2*q) / (2 * N))
        #zc_seq = np.roll(zc_seq, q)
        #zc_seq = np.concatenate([zc_seq,zc_seq_conj])
        #zc_seq = zc_seq_conj
        
 #       zc_seq = np.concatenate([zc_seq,zc_seq_conj, zc_zeros_padding])
        return zc_seq
    def calculate_time_to_next_packet(self):
        randNumber = np.random.random()
        if randNumber >= 0.99:
            randNumber = 0.99
        return -1e9 * np.log(1 - randNumber) / self.inter_arrival_time_mean # Time in ns

    def work(self, input_items, output_items):
        timeNow = time.time_ns()
        
        noutput_items = len(output_items[0])  # Number of output items to produce
        #print(noutput_items)
        output_items[0][:] = 0
        if self.transmitting:
            #print(f'counter: {self.counter}')
            if timeNow < self.packet_end_time:
                for i in range(noutput_items):    
                    output_items[0][i] = self.ZC_sequence[self.counter]#[self.counter]
                    self.counter +=1
                    if self.counter == len(self.ZC_sequence):
                        self.counter = 0
                
            else:
                if self.counter != 0:
                    for i in range(noutput_items):    
                        output_items[0][i] = self.ZC_sequence[self.counter]#[self.counter]
                        self.counter +=1
                        if self.counter == len(self.ZC_sequence):
                            self.counter = 0
                            break
                else: 
                    self.transmitting = False
                    self.time_to_next_packet = self.calculate_time_to_next_packet()
                    self.last_packet_time = timeNow
                #self.counter = 0
                
        else:
            if timeNow - self.last_packet_time >= self.time_to_next_packet:
                self.transmitting = True
                self.packet_end_time = timeNow + self.tau * 1e9
                #output_items[0][i] = self.ZC_sequence#[self.counter]
                self.counter =0
        
        return len(output_items[0])




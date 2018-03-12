from includes import *

#################### "includes" imports:
#
#   from read_data import *
#   
#   import torch
#   from torch.autograd import Variable
#   import torch.nn as nn
#   import torch.optim as optim
#
#   dtype = torch.cuda.FloatTensor # torch.FloatTensor
#
#   all_files = [h5py.File(m, 'r') for m in mat_names]
#   all_ims = [f['image'] for f in all_files]
#   all_types = [f['type'] for f in all_files]
#
####################

#from torch.nn.utils.rnn import pack_padded_sequence as ppseq
from collections import OrderedDict

class VanillaRNN(nn.Module):

    _default_num_classes = 4

    #def

    def sequence_loss(loss_fn, outputs, labels):
        '''
        returns a loss, which prioritizes the latest outputs
        '''
        pass
        #weights = np.array
        #loss = loss_fn(outputs[0,:], labels[0])
        #for i in range(1, leb(labels)):
        #    loss += 


    def __init__(self,
            num_electrodes = 22,
            conv_layers = False,
            initial_hidden_layer_sizes = [],
            recurrent_hidden_size = _default_num_classes,
            recurrent_layer_num = 1,
                # generally recommended 2/3, but in class we used 1
            recurrent_use_bias = False,
            final_hidden_layer_sizes = [], # not including num_classes output layer
            num_classes = _default_num_classes
            ):

        super(VanillaRNN, self).__init__()

        self.num_classes = num_classes
        self.conv_layers = conv_layers

        prev_size = num_electrodes

        # convolutional processing layers -- optional --
        
        if (self.conv_layers):
            self.layer1 = nn.Sequential(
                nn.Conv1d(22, 32, kernel_size=5, padding=2, stride=1), #32x1000
                nn.BatchNorm1d(32), 
                nn.ReLU(),
                nn.MaxPool1d(2)) #32 x 500
            #self.layer2 = nn.Sequential(
            #    nn.Conv1d(32, 8, kernel_size=4, padding=1, stride=2), #8x250
            #    nn.BatchNorm1d(8),
            #    nn.ReLU())

            prev_size = 32

        # input processing layers -- optional --

        # first layers converts the eeg channels to feature vectors for
        # the rnn input
        # these layers are all fully connected
        initial_layers = OrderedDict() 
        for idx, s in enumerate(initial_hidden_layer_sizes):
            initial_layers['initial_lin_{}'.format(idx)] = nn.Linear(prev_size, s)
            initial_layers['initial_relu_{}'.format(idx)] = nn.ReLU()
            prev_size = s

        self.initial_layer = nn.Sequential(initial_layers)

        # the recurrent layers
        self.rnn_layer = nn.RNN(
                            input_size = prev_size, 
                            hidden_size = recurrent_hidden_size,
                            num_layers = recurrent_layer_num,
                            bias = recurrent_use_bias,
                            batch_first = False)

        prev_size = recurrent_hidden_size

        # output processing layers -- optional --
        output_layers = OrderedDict() 
        for idx, s in enumerate(final_hidden_layer_sizes):
            output_layers['final_lin_{}'.format(idx)] = nn.Linear(prev_size, s)
            output_layers['final_relu_{}'.format(idx)] = nn.ReLU()
            prev_size = s

        # output classifier layers
        output_layers['output'] = nn.Linear(prev_size, num_classes)

        self.output_layer = nn.Sequential(output_layers)

        d = self.rnn_layer.state_dict()
        for k in d:
            if 'hh' in k:
                w = d[k].data
                d[k].data = dtype(np.identity(w.shape[0]))
        

    def forward(self, X):
        '''
        X should have shape (num samples, num_sensors=25, seq_len=1000)
        '''
        N, E, T = X.shape

        out = X

        if (self.conv_layers):
            out = self.layer1(out)
            #out = self.layer2(out)

        # for rnn, we need to permute the input
        #   before it was N, E, T
        #   it needs to be T, N, E for rnn
        print('outshape1 {}'.format(out.shape))
        out = out.permute(2,0,1) # has shape T, N, E
        print('outshape2 {}'.format(out.shape))

        out = self.initial_layer(out) # has shape T, N, H_in
        # H_in is the last hidden network layer size

        initial_state = dtype(np.ones((1, out.shape[1],out.shape[2]))/float(out.shape[2]))
        out, h = self.rnn_layer(out, initial_state) # now has shape T, N, H_rnn
        # H_rnn is the size of the hidden output

        out = self.output_layer(out) # now has shape T, N, num_classes
        print('outshape {}'.format(out.shape))

        out = out[-1,:,:]

        return out, h

        #if (self.training):
        #    reshaped_out = out.view(-1, self.num_classes)
        #    print('not reshaped outshape {}'.format(out.shape))
        #    print('reshaped outshape {}'.format(reshaped_out.shape))
        #    return reshaped_out, h
        #else:
        #    renamed = out
        #    accumulated_out = torch.mean(renamed, dim=0)
        #    print('accumulated outshape {}'.format(accumulated_out.shape))
        #    return accumulated_out, h #out[-1,:,:], h
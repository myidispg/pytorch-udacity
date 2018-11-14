#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 14 11:04:50 2018

@author: myidispg
"""

import torch
import numpy as np

# Check if cuda is available
train_on_gpu = torch.cuda.is_available()

if not train_on_gpu:
    print('CUDA is not available, training on CPU')
else:
    print('Training on GPU!!!')
    
from torchvision import datasets
import torchvision.transforms as transforms
from torch.utils.data.sampler import SubsetRandomSampler

num_workers = 0
batch_size = 20
valid_size = 0.2 # percentage of train to use as validation set

transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5,0.5,0.5),(0.5,0.5,0.5))
        ])

train_data = datasets.CIFAR10('data', train=True, download=True, transform=transform)
test_data = datasets.CIFAR10('data', train=False, download=True, transform=transform)

# obtain indices used for validation
num_train = len(train_data) # 50000
indices = list(range(num_train)) # List of indices for all training dataset
np.random.shuffle(indices) # suffle the indices
split = int(np.floor(valid_size * num_train)) # size of valid set
train_idx, valid_idx = indices[split:], indices[:split] # Split into train and valid

# Define sampler for obtaining training and validation batches
train_sampler = SubsetRandomSampler(train_idx)
valid_sampler = SubsetRandomSampler(valid_idx)

# prepare data loaders(combine dataset and sampler)
train_loader = torch.utils.data.DataLoader(train_data, batch_size = batch_size,
                                           sampler = train_sampler, num_workers=num_workers)
test_loader = torch.utils.data.DataLoader(test_data, batch_size=batch_size,
                                        sampler=test_sampler, num_workers=num_workers)

# Specify the image classes
classes=['airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog',
         'horse', 'ship', 'truck']
# -------Visualize the data---------------
import matplotlib.pyplot as plt
%matplotlib inline

# helper function to un-normalize and display the image
def imshow(img):
    img = img/2 + 0.5
    plt.imshow(np.transpose())

# obtain one batch of training images
dataiter = iter(train_loader)
images, labels = dataiter.next()
images = images.numpy() # convert images to numpy for display

# plot the images in the batch, along with the corresponding labels
fig = plt.figure(figsize=(25, 4))
# display 20 images
for idx in np.arange(20):
    ax = fig.add_subplot(2, 20/2, idx+1, xticks=[], yticks=[])
    imshow(images[idx])
    ax.set_title(classes[labels[idx]])
    
rgb_img = np.squeeze(images[3])
channels = ['red channel', 'green channel', 'blue channel']

fig = plt.figure(figsize = (36, 36)) 
for idx in np.arange(rgb_img.shape[0]):
    ax = fig.add_subplot(1, 3, idx + 1)
    img = rgb_img[idx]
    ax.imshow(img, cmap='gray')
    ax.set_title(channels[idx])
    width, height = img.shape
    thresh = img.max()/2.5
    for x in range(width):
        for y in range(height):
            val = round(img[x][y],2) if img[x][y] !=0 else 0
            ax.annotate(str(val), xy=(y,x),
                    horizontalalignment='center',
                    verticalalignment='center', size=8,
                    color='white' if img[x][y]<thresh else 'black')
            
# -------Define the neural network
import torch.nn as nn
import torch.nn.functional as F

# Input image is 32x32x3
class Network(nn.module):
    
    def __init__(self):
        super(Network, self).__init__()
        # Sees 32x32x3 image
        self.conv1 = nn.Conv2d(3, 16, 3, padding=1)
        # Sees 16x16x16 image
        self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
        # Sees 8x8x32 image
        self.conv3 = nn.Conv2d(32, 64, 3, padding=1)
        # Max pooling. Reduces image size by half.
        self.pool = nn.MaxPool2d(2,2)
        # Fully Connected layer 1
        self.fc1 = nn.Linear(64 *4 * 4, 500)
        # 500 -> 10
        self.fc2 = nn.Linear(500, 10)
        
        self.dropout(0.25)
        
    def forward(self, x):
        x = self.pool(self.relu(self.conv1)) # output = 31x31x16 -> 16x16x16
        x = self.pool(self.relu(self.conv2)) # output = 15x15x32 -> 8x8x32
        x = self.pool(self.relu(self.conv3)) # output = 7x7x64 -> 4x4x64
        # Flattern the image output
        x = x.view(-1, 64*4*4)
        x = self.dropout(self.relu(self.fc1(x)))
        x = self.fc2(x)
        return x.size
    
model = Network()

if train_on_gpu:
    model.cuda()
    
import torch.optim as optim

criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(), lr=0.03)

# Train the network
n_epochs = 30

valid_loss_min = np.Inf # Give infinite value to valid_loss_min. Used later.

 for epoch in range(1, n_epochs+1):
     
     train_loss = 0
     valid_loss = 0
     
     # set the model to train mode
     model.train()
     for data, target in train_loader:
         if train_on_gpu:
             data, target = data.cuda(), target.cuda()
         optimizer.zero_grad()
         output = model(data)
         loss = criterion(output, target)
         loss.backward()
         optimizer.step()
         train_loss += loss.item()*data.size[0]
    
     model.eval()
     for data, target in valid_loader:
         if train_on_gpu:
             data, target = data.cuda(), target.cuda()
        output = model(data)
        loss = criterion(output, target)
        valid_loss += loss.item()*data.size[0]
        
    # Calculate average loss
    train_loss /= len(train_loader.dataset)
    valid_loss /= len(valid_loader.dataset)
    
    # print training/validation statistics 
    print('Epoch: {} \tTraining Loss: {:.6f} \tValidation Loss: {:.6f}'.format(
        epoch, train_loss, valid_loss))
    
    # save model if validation loss has decreased
    if valid_loss <= valid_loss_min:
        print('Validation loss decreased ({:.6f} --> {:.6f}).  Saving model ...'.format(
        valid_loss_min,
        valid_loss))
        torch.save(model.state_dict(), 'model_cifar.pt')
        valid_loss_min = valid_loss

# Load the model with lowest validation loss
model.load_state_dict(torch.load('model_cifar.pt'))
        
# Impact of Twitter take over by Elon Musk on its users

In this project we will be analyzing the impact of Elon Musk's take over of Twitter on its users. 
We will be using the Twitter API to collect tweets and analyze them using the Natural Language Processing. 

## Environment Setup

### CUDA drivers
For installing CUDA drivers, do it this way before the requirements.txt installation:
> pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu116

### General setup
Before we start our environment and downloading of the data, make sure to run the following command to install 
dependencies:
> pip install -r requirements.txt    
 
or 
> conda install --yes --file requirements.txt


Then also make sure to create a file `.env` in the root directory of the project and add the following lines:
```
API_KEY=<your info>
API_KEY_SECRET=<your info>
BEARER_TOKEN=<your info>
ACCESS_TOKEN=<your info>
ACCESS_TOKEN_SECRET=<your info>
```


## Data Collection
For downloading the data (tweets) you should run the file `main.py` and specify how many tweets you want to download and 
from which date you want to start downloading the tweets. The downloaded tweets will be saved in a ".csv" file in the 
data folder.